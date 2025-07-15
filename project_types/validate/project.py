import json
import logging
import typing
from typing import Any

from django.contrib.gis.geos import GEOSGeometry
from django.core.files.base import ContentFile
from django.db import models
from geojson_pydantic import Feature, FeatureCollection
from geojson_pydantic.geometries import MultiPolygon, Polygon
from osgeo import ogr
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator
from pyfirebase_mapswipe import models as firebase_models
from typing_extensions import TypedDict
from ulid import ULID

from apps.project.models import (
    Project,
    ProjectAsset,
    ProjectAssetMimetypeEnum,
    ProjectAssetTypeEnum,
    ProjectTask,
    ProjectTaskGroup,
)
from main.bulk_managers import BulkCreateManager
from project_types.base import project as base_project
from project_types.firebase import raster_tile_server_name_enum_to_firebase
from project_types.tile_map_service.base.project import create_json_dump
from project_types.validate.api_calls import ohsome
from utils.custom_options.models import CustomOption
from utils.geo.raster_tile_server.models import RasterTileServerConfig

logger = logging.getLogger(__name__)


class ValidFeature(Feature[Polygon | MultiPolygon, dict[str, Any]]): ...


class ValidateRawGroupItem(TypedDict):
    feature_ids: list[int]
    features: list[ValidFeature]


# FIXME(tnagorra): We need to refactor this codeblock
# Example: We no longer need tutorial parameter
def group_input_geometries(features: list[ValidFeature], group_size: int, tutorial: bool = False):
    groups: dict[str, ValidateRawGroupItem] = {}

    # we will simply start with min group id = 100
    group_id = 100
    group_id_string = f"g{group_id}"
    feature_count = 0
    for feature in features:
        if feature_count % (group_size + 1) == 0:
            group_id += 1
            group_id_string = f"g{group_id}"

        try:
            groups[group_id_string]
        except KeyError:
            new_feature_group: ValidateRawGroupItem = {"feature_ids": [], "features": []}
            groups[group_id_string] = new_feature_group

        # we use a new id here based on the count
        # since we are not sure that GetFID returns unique values
        if not tutorial:
            groups[group_id_string]["feature_ids"].append(feature_count)
        # In the tutorial the feature id is defined by the "screen" attribute.
        # We do this so that we can sort by the feature id later and
        # get the screens displayed in the right order on the app.
        elif feature.properties is not None:
            groups[group_id_string]["feature_ids"].append(
                feature.properties["screen"],
            )
        groups[group_id_string]["features"].append(feature)

    return groups


class ValidateObjectSourceTypeEnum(models.TextChoices):
    AOI_GEOJSON_FILE = "AOI_GEOJSON_FILE", "AOI GeoJson File"
    OBJECT_GEOJSON_URL = "OBJECT_GEOJSON_URL", "Object GeoJson URL"
    TASKING_MANAGER = "TASKING_MANAGER", "Tasking Manager"


class ValidateObjectSourceConfig(BaseModel):
    source_type: ValidateObjectSourceTypeEnum

    tasking_manager_project_id: typing.Annotated[str, Field(strict=True, pattern=r"^\d+$")] | None = None

    aoi_geometry: typing.Annotated[str, Field(strict=True, pattern=r"^\d+$")] | None = None
    ohsome_filter: typing.Annotated[str, Field(strict=True, max_length=1000)] | None = None

    # FIXME(tnagorra): Add URL validation?
    # TODO(tnagorra): Check max length
    object_geojson_url: typing.Annotated[str, Field(strict=True, max_length=1000)] | None = None

    @field_validator("source_type", mode="before")
    def ensure_source_type_enum(cls, value: str | ValidateObjectSourceTypeEnum | None):
        if isinstance(value, str):
            return ValidateObjectSourceTypeEnum(value)
        return value

    @model_validator(mode="after")
    def check_validate_data(self) -> typing.Self:
        match self.source_type:
            case ValidateObjectSourceTypeEnum.AOI_GEOJSON_FILE:
                if self.aoi_geometry is None:
                    raise ValueError("AOI Geometry File is required")
                if self.ohsome_filter is None:
                    raise ValueError("Ohsome filter is required for AOI GeoJson File")
                return self
            case ValidateObjectSourceTypeEnum.OBJECT_GEOJSON_URL:
                if self.object_geojson_url is None:
                    raise ValueError("Object GeoJSON Url is required")
                return self
            case ValidateObjectSourceTypeEnum.TASKING_MANAGER:
                if self.tasking_manager_project_id is None:
                    raise ValueError("Tasking Manager Project ID is required")
                if self.ohsome_filter is None:
                    raise ValueError("Ohsome filter is required")
                return self


class ValidateProjectProperty(base_project.BaseProjectProperty):
    tile_server_property: RasterTileServerConfig
    object_source: ValidateObjectSourceConfig
    custom_options: list[CustomOption] | None = None


class ValidateProjectTaskGroupProperty(base_project.BaseProjectTaskGroupProperty): ...


class ValidateProjectTaskProperty(base_project.BaseProjectTaskProperty):
    # TODO(tnagorra): We might need to rename this to ohsome_feature_id
    task_id: str
    # TODO(tnagorra): We need to define the type for properties
    properties: dict[str, Any]
    # NOTE: We need to send geometry to firebase
    # geometry: str


# FIXME(tnagorra): Move this to project_types/firebase but getting circular dependencies error
def validate_source_type_enum_to_firebase(
    input_enum: ValidateObjectSourceTypeEnum,
) -> firebase_models.FbEnumValidateInputType:
    match input_enum:
        case ValidateObjectSourceTypeEnum.AOI_GEOJSON_FILE:
            return firebase_models.FbEnumValidateInputType.AOI_FILE
        case ValidateObjectSourceTypeEnum.OBJECT_GEOJSON_URL:
            return firebase_models.FbEnumValidateInputType.LINK
        case ValidateObjectSourceTypeEnum.TASKING_MANAGER:
            return firebase_models.FbEnumValidateInputType.TMID


class ValidateProject(
    base_project.BaseProject[
        ValidateProjectProperty,
        ValidateProjectTaskGroupProperty,
        ValidateProjectTaskProperty,
        list[ValidFeature],
        ValidateRawGroupItem,
    ],
):
    project_property_class = ValidateProjectProperty
    project_task_group_property_class = ValidateProjectTaskGroupProperty
    project_task_property_class = ValidateProjectTaskProperty

    def __init__(self, project: Project):
        super().__init__(project)

    def _process_polygons(self, geojson_data: dict[str, Any]) -> list[ValidFeature]:
        """We only want polygon and multipolygon features"""
        try:
            fc = FeatureCollection(**geojson_data)
        except ValidationError as e:
            raise ValueError("Invalid GeoJSON FeatureCollection") from e

        polygon_types = (Polygon, MultiPolygon)
        filtered_features: list[ValidFeature] = [
            feature for feature in fc.features if isinstance(feature.geometry, polygon_types)
        ]

        return filtered_features

    def _validate_aoi_geojson_file(self):
        if self.project_type_specifics.object_source.source_type != ValidateObjectSourceTypeEnum.AOI_GEOJSON_FILE:
            raise Exception("Invalid object source type for validate geojson file")

        if self.project_type_specifics.object_source.aoi_geometry is None:
            raise Exception("AOI Geometry is missing for validate geojson file")

        if self.project_type_specifics.object_source.ohsome_filter is None:
            raise Exception("Ohsome filter is missing for validate geojson file")

        aoi_asset = ProjectAsset.usable_objects().get(
            id=self.project_type_specifics.object_source.aoi_geometry,
            type=ProjectAssetTypeEnum.INPUT,
            mimetype=ProjectAssetMimetypeEnum.GEOJSON,
            project_id=self.project.pk,
        )

        with aoi_asset.file.open() as aoi_file:
            geojson = json.loads(aoi_file.read())

        feature_collection = FeatureCollection(**geojson)
        ohsome_request = {
            "endpoint": "elements/geometry",
            "filter": self.project_type_specifics.object_source.ohsome_filter,
        }

        geojson_result = ohsome(
            ohsome_request,
            feature_collection.model_dump_json(),
            properties="tags, metadata",
        )

        return self._process_polygons(geojson_data=geojson_result)

    @typing.override
    def validate(self) -> list[ValidFeature]:
        """Validate project before creating groups"""
        self.project.update_processing_status(Project.ProcessingStatus.VALIDATING_GEOMETRY, True)

        if self.project_type_specifics.object_source.source_type == ValidateObjectSourceTypeEnum.AOI_GEOJSON_FILE:
            return self._validate_aoi_geojson_file()

        # TODO(frozenhelium): implement other source types
        raise Exception("Only AOI Geojson file source type is currently implemented")

    @typing.override
    def create_tasks(self, group: ProjectTaskGroup, raw_group: ValidateRawGroupItem) -> int:
        """Create tasks for a group."""
        bulk_mgr = BulkCreateManager(chunk_size=1000)

        tasks_count = 0
        features = raw_group["features"]
        f_ids = raw_group["feature_ids"]

        for i, f_id in enumerate(f_ids):
            feature = features[i]

            if feature.geometry is not None:
                geom = ogr.CreateGeometryFromJson(
                    feature.geometry.model_dump_json(),
                )

                if geom.GetCoordinateDimension() == 3:
                    geom.FlattenTo2D()

                geometry_str = geom.ExportToWkt()

                bulk_mgr.add(
                    ProjectTask(
                        task_group_id=group.pk,
                        geometry=geometry_str,
                        project_type_specifics=self.project_task_property_class(
                            task_id=f"t{f_id}",
                            properties=feature.properties or {},
                        ).model_dump(),
                    ),
                )
                tasks_count += 1

        bulk_mgr.done()
        return tasks_count

    @typing.override
    def create_groups(self, resp: list[ValidFeature]):
        self.project.update_processing_status(Project.ProcessingStatus.GENERATING_GROUPS_AND_TASKS, True)
        raw_groups = group_input_geometries(resp, self.project.group_size)

        for _, raw_group in raw_groups.items():
            new_group = ProjectTaskGroup.objects.create(
                project_id=self.project.pk,
                number_of_tasks=0,
                progress=0,
                finished_count=0,
                required_count=0,
                project_type_specifics=self.project_task_group_property_class().model_dump(),
            )

            # Create new tasks for this group
            total_tasks = self.create_tasks(new_group, raw_group)
            logger.info("Created %s tasks for group: %s", total_tasks, new_group.pk)

    @typing.override
    def post_create_groups(self):
        # NOTE: Create a geojson from the tasks (useful for tutorial creation)
        self.project.update_processing_status(Project.ProcessingStatus.GENERATING_TASKS_GEOJSON, True)

        tasks_qs = ProjectTask.objects.filter(task_group__project_id=self.project.pk)

        def get_feature(task: ProjectTask):
            geom = GEOSGeometry(task.geometry)
            geojson = json.loads(geom.geojson)

            return {
                "type": "Feature",
                "geometry": geojson,
                "properties": {
                    "group_id": task.task_group_id,
                    "task_id": task.pk,
                },
            }

        feature_collection = {
            "type": "FeatureCollection",
            "metadata": {
                "project_id": self.project.pk,
            },
            "features": [get_feature(task) for task in tasks_qs],
        }
        file = ContentFile(
            create_json_dump(feature_collection),
            "processed_geometry.geojson",
        )

        asset = ProjectAsset.objects.create(
            client_id=str(ULID()),
            project=self.project,
            file=file,
            type=ProjectAssetTypeEnum.OUTPUT,
            mimetype=ProjectAssetMimetypeEnum.GEOJSON,
            # FIXME(tnagorra): Maybe create a internal user like mapswipe-bot
            created_by=self.project.modified_by,
            modified_by=self.project.modified_by,
        )
        self.project.project_type_specific_output = asset
        self.project.save(update_fields=("project_type_specific_output",))

    @typing.override
    def get_task_project_specifics_for_firebase(self, task):
        return firebase_models.FbMappingTaskValidateCreateOnlyInput(
            # FIXME(tnagorra): We should use task_old_fashioned_id
            taskId=str(task.pk),
            # FIXME(tnagorra): Check if we need to convert this?
            geojson=task.geometry,
        )

    @typing.override
    def get_group_project_specifics_for_firebase(self, group):
        return firebase_models.FbMappingGroupValidateCreateOnlyInput(
            # FIXME(tnagorra): We should use group_old_fashioned_id
            groupId=str(group.pk),
        )

    @typing.override
    def get_project_specifics_for_firebase(self):
        tsp = self.project_type_specifics.tile_server_property
        custom_opts = self.project_type_specifics.custom_options
        obj_source = self.project_type_specifics.object_source
        return firebase_models.FbProjectValidateCreateOnlyInput(
            customOptions=[
                firebase_models.FbObjCustomOption(
                    title=opt.title,
                    description=opt.description,
                    value=opt.value,
                    icon=opt.icon.value,
                    iconColor=opt.icon_color,
                    subOptions=[
                        firebase_models.FbBaseObjCustomSubOption(
                            value=sub_opt.value,
                            description=sub_opt.description,
                        )
                        for sub_opt in opt.sub_options
                    ]
                    if opt.sub_options is not None
                    else firebase_models.UNDEFINED,
                )
                for opt in custom_opts
            ]
            if custom_opts is not None
            else firebase_models.UNDEFINED,
            filter=obj_source.ohsome_filter or firebase_models.UNDEFINED,
            inputType=validate_source_type_enum_to_firebase(
                obj_source.source_type,
            ),
            TMId=str(obj_source.tasking_manager_project_id)
            if obj_source.tasking_manager_project_id
            else firebase_models.UNDEFINED,
            tileServer=firebase_models.FbObjRasterTileServer(
                name=raster_tile_server_name_enum_to_firebase(tsp.name),
                credits=tsp.get_config()["credits"],
                url=tsp.get_config()["raw_url"],
                apiKey=tsp.get_config()["api_key"],
                # NOTE: wmtsLayerName is deprecated as singergise is not longer supported
                wmtsLayerName=firebase_models.UNDEFINED,
            ),
        )

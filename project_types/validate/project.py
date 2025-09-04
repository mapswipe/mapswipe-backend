import json
import logging
import typing
from typing import Any

import requests
from django.contrib.gis.geos import GEOSGeometry
from django.core.files.base import ContentFile
from django.db import models
from geojson_pydantic import Feature, FeatureCollection
from geojson_pydantic.geometries import MultiPolygon, Polygon
from osgeo import ogr
from pydantic import BaseModel, ValidationError, field_validator, model_validator
from pyfirebase_mapswipe import models as firebase_models
from ulid import ULID

from apps.common.models import (
    AssetMimetypeEnum,
    AssetTypeEnum,
)
from apps.project.models import (
    Project,
    ProjectAsset,
    ProjectAssetInputTypeEnum,
    ProjectTask,
    ProjectTaskGroup,
)
from main.bulk_managers import BulkCreateManager
from main.config import Config
from project_types.base import project as base_project
from project_types.tile_map_service.base.project import create_json_dump
from project_types.validate.api_calls import ohsome
from utils import fields as custom_fields
from utils.common import Grouping, clean_up_none_keys, to_groups
from utils.custom_options.models import CustomOption
from utils.geo.raster_tile_server.models import RasterTileServerConfig

logger = logging.getLogger(__name__)


class ValidFeature(Feature[Polygon | MultiPolygon, dict[str, Any]]): ...


class ValidateObjectSourceTypeEnum(models.TextChoices):
    AOI_GEOJSON_FILE = "AOI_GEOJSON_FILE", "AOI GeoJson File"
    OBJECT_GEOJSON_URL = "OBJECT_GEOJSON_URL", "Object GeoJson URL"
    TASKING_MANAGER = "TASKING_MANAGER", "Tasking Manager"

    def to_firebase(self) -> firebase_models.FbEnumValidateInputType:
        match self:
            case ValidateObjectSourceTypeEnum.AOI_GEOJSON_FILE:
                return firebase_models.FbEnumValidateInputType.AOI_FILE
            case ValidateObjectSourceTypeEnum.OBJECT_GEOJSON_URL:
                return firebase_models.FbEnumValidateInputType.LINK
            case ValidateObjectSourceTypeEnum.TASKING_MANAGER:
                return firebase_models.FbEnumValidateInputType.TMID


class ValidateObjectSourceConfig(BaseModel):
    source_type: ValidateObjectSourceTypeEnum
    tasking_manager_project_id: custom_fields.PydanticId | None = None
    aoi_geometry: custom_fields.PydanticId | None = None
    ohsome_filter: custom_fields.PydanticLongText | None = None
    object_geojson_url: custom_fields.PydanticUrl | None = None

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
                    raise ValueError("Object GeoJSON URL is required")
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


class ValidateProject(
    base_project.BaseProject[
        ValidateProjectProperty,
        ValidateProjectTaskGroupProperty,
        ValidateProjectTaskProperty,
        list[ValidFeature],
        Grouping[ValidFeature],
    ],
):
    project_property_class = ValidateProjectProperty
    project_task_group_property_class = ValidateProjectTaskGroupProperty
    project_task_property_class = ValidateProjectTaskProperty

    def __init__(self, project: Project):
        super().__init__(project)

    def _process_polygons(self, geojson_data: dict[str, Any]) -> list[ValidFeature]:
        """We only want polygon and multipolygon features."""
        try:
            fc = FeatureCollection.model_validate(geojson_data)
        except ValidationError as e:
            raise ValueError("Invalid GeoJSON FeatureCollection") from e

        polygon_types = (Polygon, MultiPolygon)
        filtered_features: list[ValidFeature] = [
            feature for feature in fc.features if isinstance(feature.geometry, polygon_types)
        ]

        return filtered_features

    def _get_object_geometry_from_ohsome(self, geojson: Any):
        # FIXME(frozenhelium): add appropriate typing for geojson
        # FIXME(tnagorra): Check if object spreading works with nested object and validation
        feature_collection = FeatureCollection.model_validate(geojson)
        ohsome_request = {
            "endpoint": "elements/geometry",
            "filter": self.project_type_specifics.object_source.ohsome_filter,
        }

        return ohsome(
            ohsome_request,
            feature_collection.model_dump_json(),
            properties="tags, metadata",
        )

    def _validate_aoi_geojson_file(self):
        # FIXME: we need to move this outside of json
        if self.project_type_specifics.object_source.source_type != ValidateObjectSourceTypeEnum.AOI_GEOJSON_FILE:
            raise Exception("Invalid object source type for validate geojson file")

        if self.project_type_specifics.object_source.aoi_geometry is None:
            raise Exception("AOI Geometry is missing for validate geojson file")

        if self.project_type_specifics.object_source.ohsome_filter is None:
            raise Exception("Ohsome filter is missing for validate geojson file")

        aoi_asset = ProjectAsset.usable_objects().get(
            id=self.project_type_specifics.object_source.aoi_geometry,
            type=AssetTypeEnum.INPUT,
            input_type=ProjectAssetInputTypeEnum.AOI_GEOMETRY,
            project_id=self.project.pk,
        )

        with aoi_asset.file.open() as aoi_file:
            aoi_geojson = json.loads(aoi_file.read())

        geojson_result = self._get_object_geometry_from_ohsome(aoi_geojson)

        return self._process_polygons(geojson_data=geojson_result)

    def _validate_object_geojson_url(self):
        url = self.project_type_specifics.object_source.object_geojson_url
        if url is None:
            raise Exception("Object Geojson URL is missing")

        logger.info("Fetching object geojson from %s", url)

        # FIXME(frozenhelium): use predefined timeout duration
        response = requests.get(url, timeout=500)
        if response.status_code != 200:
            logger.warning("Failed to fetch object geojson from %s", url)

        logger.info("Successfully fetched object geojson from %s", url)
        geojson = response.json()

        return self._process_polygons(geojson)

    def _validate_tasking_manager(self):
        hot_tm_id = self.project_type_specifics.object_source.tasking_manager_project_id

        if hot_tm_id is None:
            raise Exception("HOT Tasking Manager Project ID is missing")

        hot_tm_url = f"{Config.HOT_TASKING_MANAGER_PROJECT_API_LINK}projects/{hot_tm_id}/queries/aoi/?as_file=false"

        # FIXME(frozenhelium): use predefined timeout duration
        aoi_result = requests.get(hot_tm_url, timeout=500)
        if aoi_result.status_code != 200:
            logger.warning("Failed to fetch AOI geojson from HOT for tm_id %s", hot_tm_id)

        logger.info("Successfully fetched AOI geojson from HOT for tm_id %s", hot_tm_id)

        aoi_geometry = aoi_result.json()
        aoi_geojson = {
            "type": "FeatureCollection",
            "metadata": {
                "project_id": self.project.pk,
                "hot_tm_project_id": hot_tm_id,
            },
            "features": [
                {
                    "type": "Feature",
                    "geometry": aoi_geometry,
                    "properties": {
                        "hot_tm_project_id": hot_tm_id,
                    },
                },
            ],
        }

        geojson_result = self._get_object_geometry_from_ohsome(aoi_geojson)

        return self._process_polygons(geojson_data=geojson_result)

    @typing.override
    def validate(self) -> list[ValidFeature]:
        """Validate project before creating groups."""
        self.project.update_processing_status(Project.ProcessingStatus.VALIDATING_GEOMETRY, True)

        if self.project_type_specifics.object_source.source_type == ValidateObjectSourceTypeEnum.AOI_GEOJSON_FILE:
            return self._validate_aoi_geojson_file()

        if self.project_type_specifics.object_source.source_type == ValidateObjectSourceTypeEnum.OBJECT_GEOJSON_URL:
            return self._validate_object_geojson_url()

        if self.project_type_specifics.object_source.source_type == ValidateObjectSourceTypeEnum.TASKING_MANAGER:
            return self._validate_tasking_manager()

        raise Exception("Invalid object source type")

    @typing.override
    def create_tasks(self, group: ProjectTaskGroup, raw_group: Grouping[ValidFeature]) -> int:
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
                        firebase_id=f"t{f_id}",
                        task_group_id=group.pk,
                        geometry=geometry_str,
                        project_type_specifics=clean_up_none_keys(
                            self.project_task_property_class(
                                task_id=f"t{f_id}",
                                properties=feature.properties or {},
                            ).model_dump(),
                        ),
                    ),
                )
                tasks_count += 1

        bulk_mgr.done()
        return tasks_count

    @typing.override
    def create_groups(self, resp: list[ValidFeature]):
        self.project.update_processing_status(Project.ProcessingStatus.GENERATING_GROUPS_AND_TASKS, True)
        raw_groups = to_groups(resp, self.project.group_size)

        for group_key, raw_group in raw_groups.items():
            new_group = ProjectTaskGroup.objects.create(
                firebase_id=group_key,
                project_id=self.project.pk,
                number_of_tasks=0,
                progress=0,
                finished_count=0,
                required_count=0,
                project_type_specifics=clean_up_none_keys(self.project_task_group_property_class().model_dump()),
            )

            # Create new tasks for this group
            total_tasks = self.create_tasks(
                group=new_group,
                raw_group=raw_group,
            )
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
                    # FIXME(tnagorra): revisit this, should we use firebase_id
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
            file_size=file.size,
            type=AssetTypeEnum.OUTPUT,
            mimetype=AssetMimetypeEnum.GEOJSON,
            # FIXME(tnagorra): Maybe create a internal user like mapswipe-bot
            created_by=self.project.modified_by,
            modified_by=self.project.modified_by,
        )
        self.project.project_type_specific_output_asset = asset
        self.project.save(update_fields=("project_type_specific_output_asset",))

    @typing.override
    def get_max_time_spend_percentile(self) -> float:
        return 6.1

    # FIREBASE

    @typing.override
    def compress_tasks_on_firebase(self) -> bool:
        return True

    @typing.override
    def get_task_specifics_for_firebase(self, task: ProjectTask):
        assert task.geometry is not None, "Task geometry must not be None"
        return firebase_models.FbMappingTaskValidateCreateOnlyInput(
            taskId=task.firebase_id,
            geojson=json.loads(task.geometry.geojson),
        )

    @typing.override
    def get_group_specifics_for_firebase(self, group: ProjectTaskGroup):
        return firebase_models.FbMappingGroupValidateCreateOnlyInput(
            groupId=group.firebase_id,
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
                    icon=str(opt.icon.label),
                    iconColor=opt.icon_color,
                    subOptions=[
                        firebase_models.FbBaseObjCustomSubOption(
                            value=sub_opt.value,
                            description=sub_opt.description,
                        )
                        for sub_opt in opt.sub_options
                    ]
                    if opt.sub_options is not None
                    else None,
                )
                for opt in custom_opts
            ]
            if custom_opts is not None
            else None,
            filter=obj_source.ohsome_filter,
            inputType=obj_source.source_type.to_firebase(),
            TMId=str(obj_source.tasking_manager_project_id) if obj_source.tasking_manager_project_id else None,
            tileServer=firebase_models.FbObjRasterTileServer(
                name=tsp.name.to_firebase(),
                credits=tsp.get_config()["credits"],
                url=tsp.get_config()["raw_url"],
                apiKey=tsp.get_config()["api_key"],
                wmtsLayerName=None,
            ),
        )

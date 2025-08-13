import json
import logging
import typing
from typing import Any, TypedDict

from django.contrib.gis.geos import GEOSGeometry
from django.core.files.base import ContentFile
from geojson_pydantic import Feature
from geojson_pydantic.geometries import MultiPolygon, Polygon
from osgeo import ogr
from pydantic import BaseModel, Field
from pyfirebase_mapswipe import models as firebase_models
from ulid import ULID

from apps.common.models import AssetMimetypeEnum, AssetTypeEnum
from apps.project.models import Project, ProjectAsset, ProjectTask, ProjectTaskGroup, ProjectTypeEnum
from main.bulk_managers import BulkCreateManager
from project_types.base import project as base_project
from project_types.street.api_calls import get_image_metadata
from utils import fields as custom_fields
from utils.common import create_json_dump
from utils.custom_options.models import CustomOption

logger = logging.getLogger(__name__)


class ValidFeature(Feature[Polygon | MultiPolygon, dict[str, Any]]): ...


class ValidateRawGroupItem(TypedDict):
    feature_ids: list[int]
    features: list[ValidFeature]


def group_input_geometries(features: list[ValidFeature], group_size: int, tutorial: bool = False):
    groups: dict[str, ValidateRawGroupItem] = {}

    # we will simply start with min group id = 100
    group_id = 100
    group_id_string = f"g{group_id}"
    for feature_count, feature in enumerate(features):
        feature_id = feature_count + 1
        if feature_id % (group_size + 1) == 0:
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
            groups[group_id_string]["feature_ids"].append(feature_id)
        # In the tutorial the feature id is defined by the "screen" attribute.
        # We do this so that we can sort by the feature id later and
        # get the screens displayed in the right order on the app.
        elif feature.properties is not None:
            groups[group_id_string]["feature_ids"].append(
                feature.properties["screen"],
            )
        groups[group_id_string]["features"].append(feature)

    return groups


class StreetMappilaryImageFilters(BaseModel):
    is_pano: bool | None = Field(
        default=None,
        description="Filter for images that are panoramas.",
    )
    creator_id: int | None = Field(
        default=None,
        description="Filter for images created by a specific user.",
    )
    organization_id: str | None = Field(
        default=None,
        description="Filter for images that belong to a specific organization.",
    )
    start_time: str | None = Field(
        default=None,
        description="Filter for images captured after this timestamp.",
    )
    end_time: str | None = Field(
        default=None,
        description="Filter for images captured before this timestamp.",
    )
    randomize_order: bool = Field(
        default=False,
        description="Randomize the order of the images.",
    )
    sampling_threshold: int | None = Field(
        default=None,
        description="Sampling threshold for filtering images.",
    )


class StreetProperty(base_project.BaseProjectProperty):
    aoi_geometry: custom_fields.PydanticId
    custom_options: list[CustomOption] | None = None
    mappilary_image_filters: StreetMappilaryImageFilters


class StreetTaskGroupProperty(base_project.BaseProjectTaskGroupProperty): ...


class StreetTaskProperty(base_project.BaseProjectTaskProperty):
    task_id: str
    group_id: str
    geometry: str


class StreetProject(
    base_project.BaseProject[
        StreetProperty,
        StreetTaskGroupProperty,
        StreetTaskProperty,
        list[ValidFeature],
        ValidateRawGroupItem,
    ],
):
    project_property_class = StreetProperty
    project_task_group_property_class = StreetTaskGroupProperty
    project_task_property_class = StreetTaskProperty

    def __init__(self, project: Project):
        super().__init__(project)
        if typing.TYPE_CHECKING:
            assert project.project_type == ProjectTypeEnum.STREET, f"{type(self)} is defined for STREET"

    @typing.override
    def validate(self) -> list[ValidFeature]:
        """Validate project before creating groups"""
        self.project.update_processing_status(Project.ProcessingStatus.VALIDATING_GEOMETRY, True)

        aoi_asset = ProjectAsset.usable_objects().get(
            id=self.project_type_specifics.aoi_geometry,
            type=AssetTypeEnum.INPUT,
            mimetype=AssetMimetypeEnum.GEOJSON,
            project_id=self.project.pk,
        )

        with aoi_asset.file.open() as aoi_file:
            aoi_geojson = json.loads(aoi_file.read())

        mappilary_image_filters = self.project_type_specifics.mappilary_image_filters

        image_ids, geometries = get_image_metadata(
            aoi_geojson=aoi_geojson,
            is_pano=mappilary_image_filters.is_pano,
            creator_id=mappilary_image_filters.creator_id,
            organization_id=mappilary_image_filters.organization_id,
            start_time=mappilary_image_filters.start_time,
            end_time=mappilary_image_filters.end_time,
            randomize_order=mappilary_image_filters.randomize_order,
            sampling_threshold=mappilary_image_filters.sampling_threshold,
        )

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
                        firebase_id=f"t{tasks_count + 1}",
                        task_group_id=group.pk,
                        geometry=geometry_str,
                        project_type_specifics=self.project_task_property_class(
                            task_id=f"t{f_id}",
                            group_id=f"g{group.pk}",
                            geometry=geometry_str,
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

        for group_key, raw_group in raw_groups.items():
            new_group = ProjectTaskGroup.objects.create(
                firebase_id=group_key,
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
            file_size=file.size,
            type=AssetTypeEnum.OUTPUT,
            mimetype=AssetMimetypeEnum.GEOJSON,
            # FIXME(tnagorra): Maybe create a internal user like mapswipe-bot
            created_by=self.project.modified_by,
            modified_by=self.project.modified_by,
        )
        self.project.project_type_specific_output = asset
        self.project.save(update_fields=("project_type_specific_output",))

    # FIREBASE

    @typing.override
    def skip_tasks_on_firebase(self) -> bool:
        return False

    @typing.override
    def get_task_specifics_for_firebase(self, task: ProjectTask):
        assert task.geometry is not None, "Task geometry must not be None"
        return firebase_models.FbMappingTaskStreetCreateOnlyInput(
            taskId=task.firebase_id,
            groupId=task.task_group.firebase_id,
        )

    @typing.override
    def get_group_specifics_for_firebase(self, group: ProjectTaskGroup):
        return firebase_models.FbMappingGroupStreetCreateOnlyInput(
            groupId=group.firebase_id,
        )

    @typing.override
    def get_project_specifics_for_firebase(self):
        custom_opts = self.project_type_specifics.custom_options
        return firebase_models.FbProjectStreetCreateOnlyInput(
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
        )

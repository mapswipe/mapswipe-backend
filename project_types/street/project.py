import json
import logging
import math
import typing

from django.contrib.gis.geos import GEOSGeometry
from django.core.files.base import ContentFile
from pydantic import BaseModel, Field
from pyfirebase_mapswipe import models as firebase_models
from shapely import to_wkt
from shapely.geometry.point import Point
from ulid import ULID

from apps.common.models import AssetMimetypeEnum, AssetTypeEnum
from apps.project.models import Project, ProjectAsset, ProjectTask, ProjectTaskGroup, ProjectTypeEnum
from main.bulk_managers import BulkCreateManager
from project_types.base import project as base_project
from project_types.street.api_calls import StreetRawGroupItem, get_image_metadata
from utils import fields as custom_fields
from utils.common import create_json_dump
from utils.custom_options.models import CustomOption

logger = logging.getLogger(__name__)


class StreetMapillaryImageFilters(BaseModel):
    is_pano: custom_fields.PydanticIsPano
    creator_id: custom_fields.PydanticCreatorId
    organization_id: custom_fields.PydanticOrganizationId
    start_time: custom_fields.PydanticStartTime
    end_time: custom_fields.PydanticEndTime
    randomize_order: custom_fields.PydanticRandomizeOrder
    sampling_threshold: custom_fields.PydanticSamplingThreshold


class StreetProjectProperty(base_project.BaseProjectProperty):
    aoi_geometry: typing.Annotated[str, Field(strict=True, pattern=r"^\d+$")] | None = None
    custom_options: list[CustomOption] | None = None
    mapillary_image_filters: StreetMapillaryImageFilters


class StreetTaskGroupProperty(base_project.BaseProjectTaskGroupProperty): ...


class StreetTaskProperty(base_project.BaseProjectTaskProperty):
    task_id: str
    group_id: str
    geometry: str


class StreetProject(
    base_project.BaseProject[
        StreetProjectProperty,
        StreetTaskGroupProperty,
        StreetTaskProperty,
        StreetRawGroupItem,
        list[tuple[int, Point]],
    ],
):
    project_property_class = StreetProjectProperty
    project_task_group_property_class = StreetTaskGroupProperty
    project_task_property_class = StreetTaskProperty

    def __init__(self, project: Project):
        super().__init__(project)
        if typing.TYPE_CHECKING:
            assert project.project_type == ProjectTypeEnum.STREET, f"{type(self)} is defined for STREET"

    @typing.override
    def validate(self) -> StreetRawGroupItem:
        """Validate project before creating groups"""
        self.project.update_processing_status(Project.ProcessingStatus.VALIDATING_GEOMETRY, True)

        aoi_asset = ProjectAsset.usable_objects().get(
            id=self.project_type_specifics.aoi_geometry,
            type=AssetTypeEnum.INPUT,
            project_id=self.project.pk,
        )

        with aoi_asset.file.open() as aoi_file:
            aoi_geojson = json.loads(aoi_file.read())

        mapillary_image_filters = self.project_type_specifics.mapillary_image_filters

        return get_image_metadata(
            aoi_geojson=aoi_geojson,
            is_pano=mapillary_image_filters.is_pano,
            creator_id=mapillary_image_filters.creator_id,
            organization_id=mapillary_image_filters.organization_id,
            start_time=mapillary_image_filters.start_time,
            end_time=mapillary_image_filters.end_time,
            randomize_order=mapillary_image_filters.randomize_order,
            sampling_threshold=mapillary_image_filters.sampling_threshold,
        )

    @typing.override
    def create_tasks(
        self,
        /,
        group: ProjectTaskGroup,
        raw_group: list[tuple[int, Point]],
    ) -> int:
        """Create tasks for a group."""
        bulk_mgr = BulkCreateManager(chunk_size=1000)
        tasks_count = 0

        for f_id, feature in raw_group:
            geometry_str = to_wkt(feature)

            bulk_mgr.add(
                ProjectTask(
                    firebase_id=f"t{f_id}",
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
    def create_groups(self, resp: StreetRawGroupItem):
        self.project.update_processing_status(Project.ProcessingStatus.GENERATING_GROUPS_AND_TASKS, True)
        number_of_groups = math.ceil(len(resp["ids"]) / self.project.group_size)

        for group_id in range(number_of_groups):
            start_index = group_id * self.project.group_size
            end_index = start_index + self.project.group_size

            group_features = resp["geometries"][start_index:end_index]
            group_feature_ids = resp["ids"][start_index:end_index]
            raw_group = list(zip(group_feature_ids, group_features, strict=True))
            new_group = ProjectTaskGroup.objects.create(
                firebase_id=f"g{group_id}",
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
            # FIXME(susilnem): Maybe create a internal user like mapswipe-bot
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

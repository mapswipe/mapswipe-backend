import json
import logging
import math
import typing

from django.contrib.gis.geos import GEOSGeometry
from django.core.files.base import ContentFile
from pydantic import BaseModel
from pyfirebase_mapswipe import models as firebase_models
from shapely import wkt
from ulid import ULID

from apps.common.models import AssetMimetypeEnum, AssetTypeEnum
from apps.project.models import (
    Project,
    ProjectAsset,
    ProjectAssetInputTypeEnum,
    ProjectTask,
    ProjectTaskGroup,
    ProjectTypeEnum,
)
from main.bulk_managers import BulkCreateManager
from project_types.base import project as base_project
from project_types.street.api_calls import StreetFeature, get_image_metadata
from utils import fields as custom_fields
from utils.asset_types.models import AoiGeometryAssetProperty
from utils.common import Grouping, create_json_dump
from utils.custom_options.models import CustomOption
from utils.geo.street_image_provider.models import StreetImageProvider

logger = logging.getLogger(__name__)


class StreetMapillaryImageFilters(BaseModel):
    is_pano: custom_fields.PydanticBool | None = None
    creator_id: custom_fields.PydanticLongText | None = None
    organization_id: custom_fields.PydanticLongText | None = None
    start_time: custom_fields.PydanticDate | None = None
    end_time: custom_fields.PydanticDate | None = None
    randomize_order: custom_fields.PydanticBool = False
    sampling_threshold: custom_fields.PydanticPositiveInt | None = None


class StreetProjectProperty(base_project.BaseProjectProperty):
    aoi_geometry: custom_fields.PydanticId
    custom_options: list[CustomOption] | None = None
    mapillary_image_filters: StreetMapillaryImageFilters
    image_provider: StreetImageProvider | None = None


class StreetTaskGroupProperty(base_project.BaseProjectTaskGroupProperty): ...


class StreetTaskProperty(base_project.BaseProjectTaskProperty):
    task_id: str
    group_id: str


class StreetProject(
    base_project.BaseProject[
        StreetProjectProperty,
        StreetTaskGroupProperty,
        StreetTaskProperty,
        Grouping[StreetFeature],
        Grouping[StreetFeature],
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
    def get_aoi_geometry_asset(self) -> ProjectAsset | None:
        return ProjectAsset.usable_objects().get(
            id=int(self.project_type_specifics.aoi_geometry),
            type=ProjectAsset.Type.INPUT,
            input_type=ProjectAssetInputTypeEnum.AOI_GEOMETRY,
            project_id=self.project.pk,
        )

    @typing.override
    def validate(self) -> Grouping[StreetFeature]:
        """Validate project before creating groups."""
        self.project.update_processing_status(Project.ProcessingStatus.VALIDATING_GEOMETRY, True)

        aoi_asset = self.project.aoi_geometry_input_asset
        if not aoi_asset:
            raise Exception("Could not find AOI geometry asset")

        asset_specific_data = AoiGeometryAssetProperty.model_validate(aoi_asset.asset_type_specifics)
        MAX_AOI_AREA = 20
        if asset_specific_data.area > MAX_AOI_AREA:
            raise base_project.ValidationException(f"Area for AOI Geometry must be less than {MAX_AOI_AREA} sq. km")

        with aoi_asset.file.open() as aoi_file:
            aoi_geojson = json.loads(aoi_file.read())

        mapillary_image_filters = self.project_type_specifics.mapillary_image_filters

        provider = self.project_type_specifics.image_provider

        return get_image_metadata(
            aoi_geojson=aoi_geojson,
            is_pano=mapillary_image_filters.is_pano,
            creator_id=mapillary_image_filters.creator_id,
            organization_id=mapillary_image_filters.organization_id,
            start_time=mapillary_image_filters.start_time,
            end_time=mapillary_image_filters.end_time,
            randomize_order=mapillary_image_filters.randomize_order,
            sampling_threshold=mapillary_image_filters.sampling_threshold,
            provider=provider,
        )

    @typing.override
    def create_tasks(
        self,
        /,
        group: ProjectTaskGroup,
        raw_group: Grouping[StreetFeature],
    ) -> int:
        """Create tasks for a group."""
        bulk_mgr = BulkCreateManager(chunk_size=1000)
        tasks_count = 0
        features = list(zip(raw_group["feature_ids"], raw_group["features"], strict=True))

        for f_id, feature in features:
            geometry_str = wkt.dumps(feature)

            bulk_mgr.add(
                ProjectTask(
                    firebase_id=str(f_id),
                    task_group_id=group.pk,
                    geometry=geometry_str,
                    project_type_specifics=self.project_task_property_class(
                        task_id=str(f_id),
                        group_id=group.firebase_id,
                    ).model_dump(),
                ),
            )
            tasks_count += 1

        bulk_mgr.done()
        return tasks_count

    @typing.override
    def create_groups(self, resp: Grouping[StreetFeature]):
        self.project.update_processing_status(Project.ProcessingStatus.GENERATING_GROUPS_AND_TASKS, True)
        number_of_groups = math.ceil(len(resp["feature_ids"]) / self.project.group_size)

        for group_id in range(number_of_groups):
            start_index = group_id * self.project.group_size
            end_index = start_index + self.project.group_size

            features = Grouping[StreetFeature](
                feature_ids=resp["feature_ids"][start_index:end_index],
                features=resp["features"][start_index:end_index],
            )
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
            total_tasks = self.create_tasks(
                group=new_group,
                raw_group=features,
            )
            logger.info("Created %s tasks for group: %s", total_tasks, new_group.pk)

    @typing.override
    def post_create_groups(self):
        # NOTE: Create a geojson from the tasks (useful for tutorial creation)
        self.project.update_processing_status(Project.ProcessingStatus.GENERATING_TASKS_GEOJSON, True)

        tasks_qs = ProjectTask.objects.filter(task_group__project_id=self.project.pk)

        def get_feature(task: ProjectTask):
            geom = GEOSGeometry(task.geometry, srid=4326)
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
        self.project.project_type_specific_output_asset = asset
        self.project.save(update_fields=("project_type_specific_output_asset",))

    @typing.override
    def get_max_time_spend_percentile(self) -> float:
        return 65

    # FIREBASE

    @typing.override
    def compress_tasks_on_firebase(self) -> bool:
        return True

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
        image_provider = self.project_type_specifics.image_provider
        number_of_groups = ProjectTaskGroup.objects.filter(project=self.project).count()
        return firebase_models.FbProjectStreetCreateOnlyInput(
            numberOfGroups=number_of_groups,
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
            imageProvider=firebase_models.FbObjImageProvider(
                name=image_provider.name.value if image_provider.name else "",
                url=image_provider.url if image_provider.url else None,
            )
            if image_provider
            else None,
        )

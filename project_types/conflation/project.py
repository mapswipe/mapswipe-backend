import json
import logging
import typing
from typing import Any

import requests
from django.contrib.gis.geos import GEOSGeometry
from django.core.files.base import ContentFile
from pydantic import BaseModel, model_validator
from pyfirebase_mapswipe import models as firebase_models
from ulid import ULID

from apps.common.models import (
    AssetMimetypeEnum,
    AssetTypeEnum,
)
from apps.project.models import (
    Geometry,
    Project,
    ProjectAsset,
    ProjectTask,
    ProjectTaskGroup,
)
from main.bulk_managers import BulkCreateManager
from project_types.base import project as base_project
from project_types.tile_map_service.base.project import create_json_dump
from utils import fields as custom_fields
from utils.common import Grouping, clean_up_none_keys, to_groups
from utils.custom_options.models import CustomOption
from utils.geo.raster_tile_server.models import RasterTileServerConfig
from utils.geo.transform import (
    AoiFeature,
    convert_feature_to_wkt,
    convert_json_dict_to_geometry_collection,
    get_area_of_geometry,
    get_polygon_of_extent,
)

logger = logging.getLogger(__name__)


class ConflationObjectSourceConfig(BaseModel):
    object_geojson_url: custom_fields.PydanticUrl | None = None

    @model_validator(mode="after")
    def check_validate_data(self) -> typing.Self:
        if self.object_geojson_url is None:
            raise ValueError("Object GeoJSON URL is required")
        return self


class ConflationProjectProperty(base_project.BaseProjectProperty):
    tile_server_property: RasterTileServerConfig
    object_source: ConflationObjectSourceConfig
    custom_options: list[CustomOption] | None = None


class ConflationProjectTaskGroupProperty(base_project.BaseProjectTaskGroupProperty): ...


class ConflationProjectTaskProperty(base_project.BaseProjectTaskProperty):
    # TODO(tnagorra): We might need to rename this to ohsome_feature_id
    task_id: str
    # TODO(tnagorra): We need to define the type for properties
    properties: dict[str, Any]
    # NOTE: We need to send geometry to firebase
    # geometry: str


class ConflationProject(
    base_project.BaseProject[
        ConflationProjectProperty,
        ConflationProjectTaskGroupProperty,
        ConflationProjectTaskProperty,
        list[AoiFeature],
        Grouping[AoiFeature],
    ],
):
    project_property_class = ConflationProjectProperty
    project_task_group_property_class = ConflationProjectTaskGroupProperty
    project_task_property_class = ConflationProjectTaskProperty

    def __init__(self, project: Project):
        super().__init__(project)

    # TODO: Is this used?
    @staticmethod
    def validate_object_count(count: int | None) -> int:
        if count is None or count <= 0:
            raise base_project.ValidationException(
                "AOI does not contain objects from selected filter.",
            )

        allowed_count = 100000

        if count > allowed_count:
            raise base_project.ValidationException(
                f"AOI contains more than 100,000 objects. -> {count}",
            )

        return count

    def _validate_object_geojson_url(self):
        url = self.project_type_specifics.object_source.object_geojson_url
        if url is None:
            raise base_project.ValidationException("Object Geojson URL is missing")

        logger.info("Fetching object geojson from %s", url)

        # FIXME(frozenhelium): use predefined timeout duration
        # FIXME(tnagorra): handle timeout error
        response = requests.get(url, timeout=500)
        if response.status_code != 200:
            raise base_project.ValidationException(
                f"Failed to fetch object geojson from {url}",
            )

        logger.info("Successfully fetched object geojson from %s", url)
        try:
            geojson = response.json()
        except Exception as e:
            raise base_project.ValidationException("GeoJSON URL did not respond with valid JSON") from e

        try:
            features, geometry_collection = convert_json_dict_to_geometry_collection(geojson)
        except Exception as e:
            raise base_project.ValidationException(
                "GeoJSON URL did not respond with a valid feature collection of polygon or multi-polygon",
            ) from e

        # TODO(tnagorra): Also store intermediate geometries?
        # TODO(tnagorra): Also create a input geometry?
        hull = geometry_collection.convex_hull
        hull_extent = hull.extent
        hull_bbox = get_polygon_of_extent(hull_extent)
        hull_center = hull.centroid
        area_km2 = get_area_of_geometry(geometry_collection)

        proj_aoi_geometry = self.project.aoi_geometry
        if not proj_aoi_geometry:
            aoi_geometry = Geometry(
                bbox=hull_bbox,
                centroid=hull_center,
                geometry=hull,
                total_area=area_km2,
            )
            aoi_geometry.save()
            self.project.aoi_geometry = aoi_geometry
        else:
            proj_aoi_geometry.bbox = hull_bbox
            proj_aoi_geometry.centroid = hull_center
            proj_aoi_geometry.geometry = hull
            proj_aoi_geometry.total_area = area_km2
            proj_aoi_geometry.save()
        self.project.total_area = area_km2
        self.project.bbox = hull_bbox
        self.project.centroid = hull_center
        self.project.save(update_fields=["aoi_geometry", "total_area", "bbox", "centroid"])

        # FIXME(frozenhelium): add validation for object count?

        return features

    @typing.override
    def validate(self) -> list[AoiFeature]:
        """Validate project before creating groups."""
        self.project.update_processing_status(Project.ProcessingStatus.VALIDATING_GEOMETRY, True)
        return self._validate_object_geojson_url()

    @typing.override
    def create_tasks(self, group: ProjectTaskGroup, raw_group: Grouping[AoiFeature]) -> int:
        """Create tasks for a group."""
        bulk_mgr = BulkCreateManager(chunk_size=1000)

        tasks_count = 0
        features = raw_group["features"]
        f_ids = raw_group["feature_ids"]

        for i, f_id in enumerate(f_ids):
            feature = features[i]
            geometry_str = convert_feature_to_wkt(feature)

            if geometry_str is not None:
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
    def create_groups(self, resp: list[AoiFeature]):
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

            # FIXME(tnagorra): This is not correct
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
        return firebase_models.FbMappingTaskConflationCreateOnlyInput(
            taskId=task.firebase_id,
            geojson=json.loads(task.geometry.geojson),
        )

    @typing.override
    def get_group_specifics_for_firebase(self, group: ProjectTaskGroup):
        return firebase_models.FbMappingGroupConflationCreateOnlyInput(
            groupId=group.firebase_id,
        )

    @typing.override
    def get_project_specifics_for_firebase(self):
        tsp = self.project_type_specifics.tile_server_property
        return firebase_models.FbProjectConflationCreateOnlyInput(
            # Conflation does not allow custom options
            tileServer=firebase_models.FbObjRasterTileServer(
                name=tsp.name.to_firebase(),
                credits=tsp.get_config()["credits"],
                url=tsp.get_config()["raw_url"],
                apiKey=tsp.get_config()["api_key"],
                wmtsLayerName=None,
            ),
        )

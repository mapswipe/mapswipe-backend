import json
import logging
import tempfile
import typing
from abc import ABC
from pathlib import Path

from django.contrib.gis.geos import GEOSGeometry
from django.core.files.base import ContentFile
from pydantic import BaseModel
from pyfirebase_mapswipe import extended_models as firebase_ext_models
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
from utils import fields as custom_fields
from utils.asset_types.models import AoiGeometryAssetProperty
from utils.common import clean_up_none_keys, create_json_dump
from utils.geo import tile_functions, tile_grouping
from utils.geo.raster_tile_server.models import RasterTileServerConfig

logger = logging.getLogger(__name__)


class TileMapServiceProjectProperty(base_project.BaseProjectProperty):
    zoom_level: custom_fields.PydanticRestrictedZoomLevel
    tile_server_property: RasterTileServerConfig
    aoi_geometry: custom_fields.PydanticId


class TileMapServiceProjectTaskGroupProperty(base_project.BaseProjectTaskGroupProperty):
    x_max: int
    x_min: int
    y_max: int
    y_min: int


class TileMapServiceProjectTaskProperty(base_project.BaseProjectTaskProperty):
    tile_x: int
    tile_y: int
    # NOTE: We added URL as it's used directly when creating exports
    url: str


class TileMapServiceBaseProject[
    TileMapServiceProjectPropertyTypeVar: TileMapServiceProjectProperty,
    TileMapServiceProjectTaskGroupPropertyTypeVar: TileMapServiceProjectTaskGroupProperty,
    TileMapServiceProjectTaskPropertyTypeVar: TileMapServiceProjectTaskProperty,
](
    base_project.BaseProject[
        TileMapServiceProjectPropertyTypeVar,
        TileMapServiceProjectTaskGroupPropertyTypeVar,
        TileMapServiceProjectTaskPropertyTypeVar,
        tile_grouping.AoiGeometry,
        tile_grouping.RawGroup,
    ],
    ABC,
):
    def __init__(self, project: Project):
        super().__init__(project)

    @typing.override
    def get_aoi_geometry_asset(self) -> ProjectAsset | None:
        return ProjectAsset.usable_objects().get(
            id=int(self.project_type_specifics.aoi_geometry),
            type=ProjectAsset.Type.INPUT,
            input_type=ProjectAssetInputTypeEnum.AOI_GEOMETRY,
            project_id=self.project.pk,
        )

    @typing.override
    def post_create_groups(self):
        # NOTE: Create a geojson from the tasks (useful for tutorial creation)
        self.project.update_processing_status(Project.ProcessingStatus.GENERATING_TASKS_GEOJSON, True)

        tasks_qs = ProjectTask.objects.filter(task_group__project_id=self.project.pk)

        def get_feature(task: ProjectTask):
            geom = GEOSGeometry(task.geometry, srid=4326)
            geojson = json.loads(geom.geojson)

            task_specifics = self.project_task_property_class.model_validate(task.project_type_specifics)

            return {
                "type": "Feature",
                "geometry": geojson,
                "properties": {
                    # FIXME(tnagorra): revisit if we need firebase_id
                    "group_id": task.task_group_id,
                    "task_id": task.pk,
                    "tile_x": task_specifics.tile_x,
                    "tile_y": task_specifics.tile_y,
                    "tile_z": self.project_type_specifics.zoom_level,
                },
            }

        feature_collection = {
            "type": "FeatureCollection",
            "metadata": {
                # FIXME(tnagorra): revisit if we need firebase_id
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

    def get_task_specifics_for_db(self, tile_x: int, tile_y: int) -> TileMapServiceProjectTaskProperty:
        return self.project_task_property_class(
            tile_x=tile_x,
            tile_y=tile_y,
            url=self.project_type_specifics.tile_server_property.generate_url(
                tile_x,
                tile_y,
                self.project_type_specifics.zoom_level,
            ),
        )

    @typing.override
    def create_tasks(
        self,
        group: ProjectTaskGroup,
        raw_group: tile_grouping.RawGroup,
    ) -> int:
        """Create tasks for a group."""
        bulk_mgr = BulkCreateManager(chunk_size=1000)

        tasks_count = 0
        for tile_x in range(raw_group["xMin"], raw_group["xMax"] + 1):
            for tile_y in range(raw_group["yMin"], raw_group["yMax"] + 1):
                geometry = tile_functions.geometry_from_tile_coords(
                    tile_x,
                    tile_y,
                    self.project_type_specifics.zoom_level,
                )
                bulk_mgr.add(
                    ProjectTask(
                        firebase_id=f"{self.project_type_specifics.zoom_level}-{tile_x}-{tile_y}",
                        task_group_id=group.pk,
                        geometry=geometry,
                        project_type_specifics=clean_up_none_keys(
                            self.get_task_specifics_for_db(tile_x, tile_y).model_dump(),
                        ),
                    ),
                )
                tasks_count += 1
        bulk_mgr.done()
        return tasks_count

    @typing.override
    def create_groups(self, resp: tile_grouping.AoiGeometry):
        """Create groups for project extent."""
        self.project.update_processing_status(Project.ProcessingStatus.GENERATING_GROUPS_AND_TASKS, True)

        raw_groups = tile_grouping.extent_to_groups(
            resp,
            self.project_type_specifics.zoom_level,
            self.project.group_size,
        )

        for group_key, raw_group in raw_groups.items():
            # Create new group
            # FIXME(thenav56): Bulk create here as well?
            new_group = ProjectTaskGroup.objects.create(
                firebase_id=group_key,
                project_id=self.project.pk,
                number_of_tasks=0,
                progress=0,
                finished_count=0,
                required_count=0,
                project_type_specifics=clean_up_none_keys(
                    self.project_task_group_property_class(
                        x_max=raw_group["xMax"],
                        x_min=raw_group["xMin"],
                        y_max=raw_group["yMax"],
                        y_min=raw_group["yMin"],
                    ).model_dump(),
                ),
            )
            # Create new tasks for this group
            total_tasks = self.create_tasks(new_group, raw_group)
            # FIXME(tnagorra): This is not correct
            logger.info("Created %s tasks for group: %s", total_tasks, new_group.pk)

    @typing.override
    def validate(self):
        """Validate project before creating groups."""
        self.project.update_processing_status(Project.ProcessingStatus.VALIDATING_GEOMETRY, True)

        aoi_asset = self.project.aoi_geometry_input_asset
        if not aoi_asset:
            raise Exception("Could not find AOI geometry asset")

        asset_specific_data = AoiGeometryAssetProperty.model_validate(aoi_asset.asset_type_specifics)
        allowed_area = 5 * (4 ** (23 - self.project_type_specifics.zoom_level))
        if asset_specific_data.area > allowed_area:
            raise base_project.ValidationException(f"Area for AOI Geometry must be less than {allowed_area} sq. km")

        extension = Path(aoi_asset.file.name).suffix
        with tempfile.NamedTemporaryFile(suffix=extension, dir=Config.TEMP_DIR) as temp_file:
            # FIXME(frozenhelium): close the aoi_asset file?
            with aoi_asset.file.open() as aoi_file:
                temp_file.write(aoi_file.read())
            temp_file.flush()

            return tile_grouping.get_geometry_from_file(temp_file.name)

    # FIREBASE

    @typing.override
    def skip_tasks_on_firebase(self) -> bool:
        return True

    @typing.override
    def get_task_specifics_for_firebase(self, task: ProjectTask) -> BaseModel:
        return firebase_ext_models.FbEmptyModel()

    @typing.override
    def get_group_specifics_for_firebase(
        self,
        group: ProjectTaskGroup,
    ) -> firebase_models.FbMappingGroupTileMapServiceCreateOnlyInput:
        task_group_specifics = self.project_task_group_property_class.model_validate(group.project_type_specifics)
        return firebase_models.FbMappingGroupTileMapServiceCreateOnlyInput(
            groupId=group.firebase_id,
            xMax=task_group_specifics.x_max,
            xMin=task_group_specifics.x_min,
            yMax=task_group_specifics.y_max,
            yMin=task_group_specifics.y_min,
        )

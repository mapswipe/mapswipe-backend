import logging
import tempfile
import typing
from abc import ABC
from pathlib import Path

from django.conf import settings
from pydantic import field_validator

from apps.project.models import Project, ProjectAsset, ProjectAssetTypeEnum, ProjectTask, ProjectTaskGroup
from apps.project.project_types.base import project as base_project
from main.bulk_managers import BulkCreateManager
from utils.geo import tile_functions, tile_grouping
from utils.geo.tile_server.models import TileServerConfig
from utils.geo.tile_server.tile_server import AvailableTileServerTypeAlias, get_tile_server

logger = logging.getLogger(__name__)


class TileMapServiceProjectProperty(base_project.BaseProjectProperty):
    zoom_level: int
    tile_server_property: TileServerConfig
    aoi_geometry: int | None

    @field_validator("zoom_level")
    @classmethod
    def zoom_level_range(cls, v: int):
        if v < 14:
            raise ValueError("Zoom level should at least be 14")
        if v > 22:
            raise ValueError("Zoom level should at most be 22")
        return v


class TileMapServiceProjectTaskGroupProperty(base_project.BaseProjectTaskGroupProperty):
    x_max: int
    x_min: int
    y_max: int
    y_min: int


class TileMapServiceProjectTaskProperty(base_project.BaseProjectTaskProperty):
    url: str
    tile_x: int
    tile_y: int


TileMapServiceProjectPropertyTypeVar = typing.TypeVar(
    "TileMapServiceProjectPropertyTypeVar",
    bound=TileMapServiceProjectProperty,
)
TileMapServiceProjectTaskGroupPropertyTypeVar = typing.TypeVar(
    "TileMapServiceProjectTaskGroupPropertyTypeVar",
    bound=TileMapServiceProjectTaskGroupProperty,
)
TileMapServiceProjectTaskPropertyTypeVar = typing.TypeVar(
    "TileMapServiceProjectTaskPropertyTypeVar",
    bound=TileMapServiceProjectTaskProperty,
)


class TileMapServiceBaseProject(
    base_project.BaseProject[
        TileMapServiceProjectPropertyTypeVar,
        TileMapServiceProjectTaskGroupPropertyTypeVar,
        TileMapServiceProjectTaskPropertyTypeVar,
        tile_grouping.AoiGeometry,
    ],
    ABC,
):
    tile_server: AvailableTileServerTypeAlias

    def __init__(self, project: Project):
        super().__init__(project)
        self.tile_server = get_tile_server(self.project_type_specifics.tile_server_property)

    @typing.override
    def _create_tasks(self, group: ProjectTaskGroup, raw_group: tile_grouping.RawGroup) -> int:
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
                url = self.tile_server.generate_url(
                    tile_x,
                    tile_y,
                    self.project_type_specifics.zoom_level,
                )
                bulk_mgr.add(
                    ProjectTask(
                        task_group_id=group.pk,
                        geometry=geometry,
                        project_type_specifics=self.project_task_property_class(
                            tile_x=tile_x,
                            tile_y=tile_y,
                            url=url,
                        ).model_dump(),
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

        for _, raw_group in raw_groups.items():
            # Create new group
            # TODO(thenav56): Bulk create here as well?
            new_group = ProjectTaskGroup.objects.create(
                project_id=self.project.pk,
                number_of_tasks=0,
                progress=0,
                finished_count=0,
                required_count=0,
                project_type_specifics=self.project_task_group_property_class(
                    x_max=raw_group["xMax"],
                    x_min=raw_group["xMin"],
                    y_max=raw_group["yMax"],
                    y_min=raw_group["yMin"],
                ).model_dump(),
            )
            # Create new tasks for this group
            total_tasks = self._create_tasks(new_group, raw_group)
            logger.info("Created %s tasks for group: %s", total_tasks, new_group.pk)

    @typing.override
    def validate(self):
        """Validate project before creating groups"""
        self.project.update_processing_status(Project.ProcessingStatus.VALIDATING_GEOMETRY, True)

        # TODO(tnagorra): Let's read the asset_id from project specifics
        aoi_asset = ProjectAsset.objects.get(
            project_id=self.project.id,
            asset_type=ProjectAssetTypeEnum.GEOMETRY_AOI,
        )
        file = aoi_asset.file

        extension = Path(file.name).suffix
        with tempfile.NamedTemporaryFile(suffix=extension, dir=settings.TEMP_DIR) as temp_file:
            temp_file.write(file.read())
            temp_file.flush()

            aoi_geometry = tile_grouping.get_geometry_from_file(temp_file.name)
            aoi_polygons = aoi_geometry["polygons"]

            POLYGON_COUNT_LIMIT = 20
            if len(aoi_polygons) > POLYGON_COUNT_LIMIT:
                # FIXME(tnagorra): Properly handle error
                raise base_project.ValidateException(f"No more than {POLYGON_COUNT_LIMIT} polygons please")

            # NOTE: The formula was copied from the validation in manager dashboard
            aoi_area = sum([polygon.area for polygon in aoi_polygons])
            allowed_area = 5 * (4 ** (23 - self.project_type_specifics.zoom_level))
            if aoi_area > allowed_area:
                # FIXME(tnagorra): Properly handle error
                raise base_project.ValidateException(f"No more than {allowed_area} area please")

            return aoi_geometry

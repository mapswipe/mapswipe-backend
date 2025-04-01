from apps.project.models import Project, ProjectTask, ProjectTaskGroup, ProjectTypeEnum
from apps.project.project_types.tile_map_service.base import project as base_project
from main.bulk_managers import BulkCreateManager
from utils.geo import tile_functions, tile_grouping
from utils.geo.tile_server.models import TileServerConfig
from utils.geo.tile_server.tile_server import AvailableTileServerTypeAlias, get_tile_server


class ChangeDetectionProjectProperty(base_project.TileMapServiceProjectProperty):
    tile_server_b_property: TileServerConfig


class ChangeDetectionProjectTaskGroupProperty(base_project.TileMapServiceProjectTaskGroupProperty): ...


class ChangeDetectionProjectTaskProperty(base_project.TileMapServiceProjectTaskProperty):
    url_b: str


class ChangeDetectionProject(
    base_project.TileMapServiceBaseProject[
        ChangeDetectionProjectProperty,
        ChangeDetectionProjectTaskGroupProperty,
        ChangeDetectionProjectTaskProperty,
    ],
):
    tile_server_b: AvailableTileServerTypeAlias

    project_property_class = ChangeDetectionProjectProperty
    project_task_group_property_class = ChangeDetectionProjectTaskGroupProperty
    project_task_property_class = ChangeDetectionProjectTaskProperty

    def __init__(self, project: Project):
        super().__init__(project)
        assert project.project_type == ProjectTypeEnum.CHANGE_DETECTION, f"{type(self)} is defined for CHANGE_DETECTION"
        self.tile_server_b = get_tile_server(self.project_type_specifics.tile_server_b_property)

    def _create_tasks(self, group: ProjectTaskGroup, raw_group: tile_grouping.RawGroup) -> int:
        bulk_mgr = BulkCreateManager(chunk_size=1000)

        tasks_count = 0
        for tile_x in range(raw_group["xMin"], raw_group["xMax"] + 1):
            for tile_y in range(raw_group["yMin"], raw_group["yMax"] + 1):
                geometry = tile_functions.geometry_from_tile_coords(tile_x, tile_y, self.project.zoom_level)
                url = self.tile_server.generate_url(
                    tile_x,
                    tile_y,
                    self.project.zoom_level,
                )
                # Additional
                url_b = self.tile_server_b.generate_url(
                    tile_x,
                    tile_y,
                    self.project.zoom_level,
                )
                bulk_mgr.add(
                    ProjectTask(
                        task_group_id=group.pk,
                        geometry=geometry,
                        project_type_specifics=self.project_task_property_class(
                            tile_x=tile_x,
                            tile_y=tile_y,
                            url=url,
                            # Additional
                            url_b=url_b,
                        ).model_dump(),
                    )
                )
                tasks_count += 1
        bulk_mgr.done()
        return tasks_count

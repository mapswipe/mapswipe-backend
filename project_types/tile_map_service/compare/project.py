import typing

from pydantic import BaseModel

from apps.project.models import Project, ProjectTask, ProjectTaskGroup, ProjectTypeEnum
from main.bulk_managers import BulkCreateManager
from project_types.tile_map_service.base import project as base_project
from utils import fields as custom_fields
from utils.geo import tile_functions, tile_grouping
from utils.geo.raster_tile_server.models import RasterTileServerConfig


class CompareProjectProperty(base_project.TileMapServiceProjectProperty):
    tile_server_b_property: RasterTileServerConfig


class CompareProjectTaskGroupProperty(base_project.TileMapServiceProjectTaskGroupProperty): ...


class CompareProjectTaskProperty(base_project.TileMapServiceProjectTaskProperty):
    url_b: custom_fields.PydanticUrl


class CompareProject(
    base_project.TileMapServiceBaseProject[
        CompareProjectProperty,
        CompareProjectTaskGroupProperty,
        CompareProjectTaskProperty,
    ],
):
    project_property_class = CompareProjectProperty
    project_task_group_property_class = CompareProjectTaskGroupProperty
    project_task_property_class = CompareProjectTaskProperty

    def __init__(self, project: Project):
        super().__init__(project)
        if typing.TYPE_CHECKING:
            assert project.project_type == ProjectTypeEnum.COMPARE, f"{type(self)} is defined for COMPARE"

    @typing.override
    def create_tasks(self, group: ProjectTaskGroup, raw_group: tile_grouping.RawGroup) -> int:
        bulk_mgr = BulkCreateManager(chunk_size=1000)

        tasks_count = 0
        for tile_x in range(raw_group["xMin"], raw_group["xMax"] + 1):
            for tile_y in range(raw_group["yMin"], raw_group["yMax"] + 1):
                geometry = tile_functions.geometry_from_tile_coords(
                    tile_x,
                    tile_y,
                    self.project_type_specifics.zoom_level,
                )
                url = self.project_type_specifics.tile_server_property.generate_url(
                    tile_x,
                    tile_y,
                    self.project_type_specifics.zoom_level,
                )
                # Additional
                url_b = self.project_type_specifics.tile_server_b_property.generate_url(
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
                            # Additional
                            url_b=url_b,
                        ).model_dump(),
                    ),
                )
                tasks_count += 1
        bulk_mgr.done()
        return tasks_count

    @typing.override
    def get_project_specifics_for_firebase(self, project_ref):
        class EmptyModel(BaseModel): ...

        return EmptyModel()

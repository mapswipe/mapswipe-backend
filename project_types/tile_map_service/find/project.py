import typing

from apps.project.models import Project, ProjectTypeEnum
from project_types.tile_map_service.base import project as tile_map_service_project


class FindProjectProperty(tile_map_service_project.TileMapServiceProjectProperty): ...


class FindProjectTaskGroupProperty(tile_map_service_project.TileMapServiceProjectTaskGroupProperty): ...


class FindProjectTaskProperty(tile_map_service_project.TileMapServiceProjectTaskProperty): ...


class FindProject(
    tile_map_service_project.TileMapServiceBaseProject[
        FindProjectProperty,
        FindProjectTaskGroupProperty,
        FindProjectTaskProperty,
    ],
):
    project_property_class = FindProjectProperty
    project_task_group_property_class = FindProjectTaskGroupProperty
    project_task_property_class = FindProjectTaskProperty

    def __init__(self, project: Project):
        super().__init__(project)
        if typing.TYPE_CHECKING:
            assert project.project_type == ProjectTypeEnum.FIND, f"{type(self)} is defined for FIND"

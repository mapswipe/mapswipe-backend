import typing

from apps.project.models import Project, ProjectTypeEnum
from apps.project.project_types.tile_map_service.base import project as base_project
from utils.geo.tile_server.models import TileServerConfig
from utils.geo.tile_server.tile_server import AvailableTileServerTypeAlias, get_tile_server


class CompletenessProjectProperty(base_project.TileMapServiceProjectProperty):
    tile_server_b_property: TileServerConfig


class CompletenessProjectTaskGroupProperty(base_project.TileMapServiceProjectTaskGroupProperty): ...


class CompletenessProjectTaskProperty(base_project.TileMapServiceProjectTaskProperty):
    url_b: str


class CompletenessProject(
    base_project.TileMapServiceBaseProject[
        CompletenessProjectProperty,
        CompletenessProjectTaskGroupProperty,
        CompletenessProjectTaskProperty,
    ],
):
    tile_server_b: AvailableTileServerTypeAlias

    project_property_class = CompletenessProjectProperty
    project_task_group_property_class = CompletenessProjectTaskGroupProperty
    project_task_property_class = CompletenessProjectTaskProperty

    def __init__(self, project: Project):
        super().__init__(project)
        if typing.TYPE_CHECKING:
            assert project.project_type == ProjectTypeEnum.COMPLETENESS, f"{type(self)} is defined for COMPLETENESS"
        self.tile_server_b = get_tile_server(self.project_type_specifics.tile_server_b_property)

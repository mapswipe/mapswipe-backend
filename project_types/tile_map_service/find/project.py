import typing

from pyfirebase_mapswipe import models as firebase_models

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

    @typing.override
    def get_max_time_spend_percentile(self) -> float:
        return 1.4

    @typing.override
    def get_task_specifics_for_db(self, tile_x: int, tile_y: int) -> FindProjectTaskProperty:
        return self.project_task_property_class(
            tile_x=tile_x,
            tile_y=tile_y,
            url=self.project_type_specifics.tile_server_property.generate_url(
                tile_x,
                tile_y,
                self.project_type_specifics.zoom_level,
            ),
        )

    # FIREBASE

    @typing.override
    def get_project_specifics_for_firebase(self):
        tsp = self.project_type_specifics.tile_server_property
        return firebase_models.FbProjectFindCreateOnlyInput(
            zoomLevel=self.project_type_specifics.zoom_level,
            tileServer=firebase_models.FbObjRasterTileServer(
                name=tsp.name.to_firebase(),
                credits=tsp.get_config()["credits"],
                url=tsp.get_config()["raw_url"],
                apiKey=tsp.get_config()["api_key"],
                wmtsLayerName=None,
            ),
        )

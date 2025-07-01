import typing

from pyfirebase_mapswipe import extended_models as firebase_ext_models
from pyfirebase_mapswipe import models as firebase_models

from apps.project.models import Project, ProjectTypeEnum
from project_types.firebase import raster_tile_server_name_enum_to_firebase
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
    def get_task_project_specifics_for_firebase(self, task):
        return firebase_ext_models.FbEmptyModel()

    @typing.override
    def get_group_project_specifics_for_firebase(self, group):
        return firebase_ext_models.FbEmptyModel()

    @typing.override
    def get_project_specifics_for_firebase(self):
        tsp = self.project_type_specifics.tile_server_property
        # TODO(tnagorra): Create groups
        # TODO(tnagorra): Create tasks (if necessary)
        return firebase_models.FbProjectFindCreateOnlyInput(
            zoomLevel=self.project_type_specifics.zoom_level,
            tileServer=firebase_models.FbObjRasterTileServer(
                name=raster_tile_server_name_enum_to_firebase(tsp.name),
                credits=tsp.get_credits(),
                url=tsp.get_url(),
                # NOTE: We already replace apiKey in the url so apiKey is empty
                apiKey=firebase_models.UNDEFINED,
                # NOTE: wmtsLayerName is deprecated as singergise is not longer supported
                wmtsLayerName=firebase_models.UNDEFINED,
            ),
        )

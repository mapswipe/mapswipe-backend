import typing

from pyfirebase_mapswipe import models as firebase_models

from apps.project.models import Project, ProjectTask, ProjectTypeEnum
from project_types.firebase import raster_tile_server_name_enum_to_firebase
from project_types.tile_map_service.base import project as base_project
from utils.geo.raster_tile_server.models import RasterTileServerConfig


class CompareProjectProperty(base_project.TileMapServiceProjectProperty):
    tile_server_b_property: RasterTileServerConfig


class CompareProjectTaskGroupProperty(base_project.TileMapServiceProjectTaskGroupProperty): ...


class CompareProjectTaskProperty(base_project.TileMapServiceProjectTaskProperty): ...


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
    def skip_tasks_for_firebase(self) -> bool:
        return False

    @typing.override
    def get_task_project_specifics_for_firebase(self, task: ProjectTask):
        task_specifics = self.project_task_property_class(
            **task.project_type_specifics,
        )
        tsp = self.project_type_specifics.tile_server_property
        tsp_b = self.project_type_specifics.tile_server_b_property

        return firebase_models.FbMappingTaskCompareCreateOnlyInput(
            groupId=str(task.task_group.firebase_id),
            taskId=str(task.task_group_id),
            taskX=task_specifics.tile_x,
            taskY=task_specifics.tile_y,
            url=tsp.generate_url(
                task_specifics.tile_x,
                task_specifics.tile_y,
                self.project_type_specifics.zoom_level,
            ),
            urlB=tsp_b.generate_url(
                task_specifics.tile_x,
                task_specifics.tile_y,
                self.project_type_specifics.zoom_level,
            ),
        )

    @typing.override
    def get_project_specifics_for_firebase(self):
        tsp = self.project_type_specifics.tile_server_property
        tsp_b = self.project_type_specifics.tile_server_b_property

        return firebase_models.FbProjectCompareCreateOnlyInput(
            zoomLevel=self.project_type_specifics.zoom_level,
            tileServer=firebase_models.FbObjRasterTileServer(
                name=raster_tile_server_name_enum_to_firebase(tsp.name),
                credits=tsp.get_config()["credits"],
                url=tsp.get_config()["raw_url"],
                apiKey=tsp.get_config()["api_key"],
                # NOTE: wmtsLayerName is deprecated as singergise is not longer supported
                wmtsLayerName=firebase_models.UNDEFINED,
            ),
            tileServerB=firebase_models.FbObjRasterTileServer(
                name=raster_tile_server_name_enum_to_firebase(tsp_b.name),
                credits=tsp_b.get_config()["credits"],
                url=tsp_b.get_config()["raw_url"],
                apiKey=tsp_b.get_config()["api_key"],
                # NOTE: wmtsLayerName is deprecated as singergise is not longer supported
                wmtsLayerName=firebase_models.UNDEFINED,
            ),
        )

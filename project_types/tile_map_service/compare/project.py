import typing

from pyfirebase_mapswipe import models as firebase_models

from apps.project.models import Project, ProjectTask, ProjectTypeEnum
from project_types.tile_map_service.base import project as base_project
from utils.geo.raster_tile_server.models import RasterTileServerConfig


class CompareProjectProperty(base_project.TileMapServiceProjectProperty):
    tile_server_b_property: RasterTileServerConfig


class CompareProjectTaskGroupProperty(base_project.TileMapServiceProjectTaskGroupProperty): ...


class CompareProjectTaskProperty(base_project.TileMapServiceProjectTaskProperty):
    # NOTE: We added URL as it's used directly when creating exports
    url_b: str


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

    # Compare uses one tile per task, so groups are 1x1 in tile units.
    min_tile_x_multiplier = 1
    min_tile_y_multiplier = 1

    def __init__(self, project: Project):
        super().__init__(project)
        if typing.TYPE_CHECKING:
            assert project.project_type == ProjectTypeEnum.COMPARE, f"{type(self)} is defined for COMPARE"

    @typing.override
    def get_max_time_spend_percentile(self) -> float:
        return 11.2

    @typing.override
    def get_task_specifics_for_db(self, tile_x: int, tile_y: int) -> CompareProjectTaskProperty:
        return self.project_task_property_class(
            tile_x=tile_x,
            tile_y=tile_y,
            url=self.project_type_specifics.tile_server_property.generate_url(
                tile_x,
                tile_y,
                self.project_type_specifics.zoom_level,
            ),
            url_b=self.project_type_specifics.tile_server_b_property.generate_url(
                tile_x,
                tile_y,
                self.project_type_specifics.zoom_level,
            ),
        )

    # FIREBASE

    @typing.override
    def skip_tasks_on_firebase(self) -> bool:
        return False

    @typing.override
    def get_task_specifics_for_firebase(self, task: ProjectTask) -> firebase_models.FbMappingTaskCompareCreateOnlyInput:
        task_specifics = self.project_task_property_class.model_validate(task.project_type_specifics)

        return firebase_models.FbMappingTaskCompareCreateOnlyInput(
            groupId=str(task.task_group.firebase_id),
            taskId=task.firebase_id,
            taskX=task_specifics.tile_x,
            taskY=task_specifics.tile_y,
            url=task_specifics.url,
            urlB=task_specifics.url_b,
        )

    @typing.override
    def get_project_specifics_for_firebase(self) -> firebase_models.FbProjectCompareCreateOnlyInput:
        tsp = self.project_type_specifics.tile_server_property
        tsp_b = self.project_type_specifics.tile_server_b_property

        return firebase_models.FbProjectCompareCreateOnlyInput(
            zoomLevel=self.project_type_specifics.zoom_level,
            tileServer=firebase_models.FbObjRasterTileServer(
                name=tsp.name.to_firebase(),
                credits=tsp.get_config()["credits"],
                url=tsp.get_config()["raw_url"],
                apiKey=tsp.get_config()["api_key"],
                wmtsLayerName=None,
            ),
            tileServerB=firebase_models.FbObjRasterTileServer(
                name=tsp_b.name.to_firebase(),
                credits=tsp_b.get_config()["credits"],
                url=tsp_b.get_config()["raw_url"],
                apiKey=tsp_b.get_config()["api_key"],
                wmtsLayerName=None,
            ),
        )

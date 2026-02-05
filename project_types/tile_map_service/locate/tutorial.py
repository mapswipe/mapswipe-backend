import typing

from pyfirebase_mapswipe import extended_models as firebase_ext_models
from pyfirebase_mapswipe import models as firebase_models

from apps.project.models import ProjectTypeEnum
from apps.tutorial.models import Tutorial, TutorialTask
from project_types.tile_map_service.base import tutorial as tile_map_service_tutorial

from .project import LocateProjectProperty


class LocateTutorialTaskProperty(tile_map_service_tutorial.TileMapServiceTutorialTaskProperty): ...


class LocateTutorial(
    tile_map_service_tutorial.TileMapServiceBaseTutorial[
        LocateProjectProperty,
        LocateTutorialTaskProperty,
    ],
):
    project_property_class = LocateProjectProperty
    tutorial_task_property_class = LocateTutorialTaskProperty

    def __init__(self, tutorial: Tutorial):
        super().__init__(tutorial)

    @typing.override
    def get_task_specifics_for_firebase(self, task: TutorialTask, index: int, screen: int):
        tsp = self.project_type_specifics.tile_server_property

        task_specifics = self.tutorial_task_property_class.model_validate(task.project_type_specifics)

        resp = super().get_task_specifics_for_firebase(task, index, screen)

        return firebase_ext_models.FbLocateTutorialTaskComplete(
            geometry=resp.geometry,
            groupId=resp.groupId,
            projectId=resp.projectId,
            referenceAnswer=resp.referenceAnswer,
            screen=resp.screen,
            taskId_real=resp.taskId_real,
            taskX=resp.taskX,
            taskY=resp.taskY,
            taskId=resp.taskId,
            url=tsp.generate_url(
                task_specifics.tile_x,
                task_specifics.tile_y,
                task_specifics.tile_z,
            ),
        )

    @typing.override
    def get_tutorial_specifics_for_firebase(self):
        tsp = self.project_type_specifics.tile_server_property

        projectType = ProjectTypeEnum.LOCATE.value
        assert projectType == 9, "Project Locate should be 9"

        return firebase_models.FbLocateTutorial(
            zoomLevel=self.project_type_specifics.zoom_level,
            projectType=projectType,
            subGridSize=self.project_type_specifics.sub_grid_size.to_firebase(),
            tileServer=firebase_models.FbObjRasterTileServer(
                name=tsp.name.to_firebase(),
                credits=tsp.get_config()["credits"],
                url=tsp.get_config()["raw_url"],
                apiKey=tsp.get_config()["api_key"],
                wmtsLayerName=None,
            ),
        )

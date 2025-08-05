import typing

from pyfirebase_mapswipe import extended_models as firebase_ext_models
from pyfirebase_mapswipe import models as firebase_models

from apps.project.models import ProjectTypeEnum
from apps.tutorial.models import Tutorial, TutorialTask
from project_types.tile_map_service.base import tutorial as tile_map_service_tutorial

from .project import FindProjectProperty


class FindTutorialTaskProperty(tile_map_service_tutorial.TileMapServiceTutorialTaskProperty): ...


class FindTutorial(
    tile_map_service_tutorial.TileMapServiceBaseTutorial[
        FindProjectProperty,
        FindTutorialTaskProperty,
    ],
):
    project_property_class = FindProjectProperty
    tutorial_task_property_class = FindTutorialTaskProperty

    def __init__(self, tutorial: Tutorial):
        super().__init__(tutorial)

    @typing.override
    def get_task_tutorial_specifics_for_firebase(self, task: TutorialTask, index: int):
        tsp = self.project_type_specifics.tile_server_property

        task_specifics = self.tutorial_task_property_class(
            **task.project_type_specifics,
        )

        resp = super().get_task_tutorial_specifics_for_firebase(task, index)

        return firebase_ext_models.FbFindTutorialTaskComplete(
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

        projectType = ProjectTypeEnum.FIND.value
        assert projectType == 1, "Project Find should be 1"

        return firebase_models.FbFindTutorial(
            zoomLevel=self.project_type_specifics.zoom_level,
            projectType=projectType,
            tileServer=firebase_models.FbObjRasterTileServer(
                name=tsp.name.to_firebase(),
                credits=tsp.get_config()["credits"],
                url=tsp.get_config()["raw_url"],
                apiKey=tsp.get_config()["api_key"],
                wmtsLayerName=None,
            ),
        )

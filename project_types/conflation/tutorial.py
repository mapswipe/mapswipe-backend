import json
import logging
import typing

from pyfirebase_mapswipe import extended_models as firebase_ext_models
from pyfirebase_mapswipe import models as firebase_models

from apps.project.models import ProjectTypeEnum
from apps.tutorial.models import Tutorial, TutorialTask
from project_types.base import tutorial as base_tutorial
from project_types.base.tutorial import BaseTutorialTaskProperty
from utils.geo.transform import convert_json_str_to_wkt

from .project import ConflationProjectProperty

logger = logging.getLogger(__name__)


class ConflationTutorialTaskProperty(BaseTutorialTaskProperty):
    # FIXME(tnagorra): add positive integer
    identifier: int
    # FIXME(tnagorra): Use geometry from TutorialTask
    object_geometry: str


class ConflationTutorial(
    base_tutorial.BaseTutorial[
        ConflationProjectProperty,
        ConflationTutorialTaskProperty,
    ],
):
    project_property_class = ConflationProjectProperty
    tutorial_task_property_class = ConflationTutorialTaskProperty

    def __init__(self, tutorial: Tutorial):
        super().__init__(tutorial)

    @typing.override
    def compress_tasks_on_firebase(self) -> bool:
        return True

    @typing.override
    def get_task_specifics_for_firebase(self, task: TutorialTask, index: int, screen: int):
        task_specifics = self.tutorial_task_property_class.model_validate(task.project_type_specifics)

        geojson = json.loads(task_specifics.object_geometry)
        geometry_wkt = convert_json_str_to_wkt(task_specifics.object_geometry)

        return firebase_models.FbConflationTutorialTask(
            taskId=f"t{index}",
            geojson=geojson,
            properties=firebase_models.FbConflationTutorialTaskProperties(
                id=task_specifics.identifier,
                reference=task.reference,
                screen=screen,
            ),
            geometry=geometry_wkt,
        )

    @typing.override
    def get_group_specifics_for_firebase(self):
        return firebase_ext_models.FbEmptyModel()

    @typing.override
    def get_tutorial_specifics_for_firebase(self):
        tsp = self.project_type_specifics.tile_server_property

        projectType = ProjectTypeEnum.CONFLATION.value
        assert projectType == 8, "Project Validate should be 8"

        return firebase_models.FbConflationTutorial(
            # FIXME(tnagorra): This is the path to local storage.
            inputGeometries="",
            # FIXME(tnagorra): Check if this is always 18, app is calculating zoomLevel using geometry
            zoomLevel=18,
            projectType=projectType,
            tileServer=firebase_models.FbObjRasterTileServer(
                name=tsp.name.to_firebase(),
                credits=tsp.get_config()["credits"],
                url=tsp.get_config()["raw_url"],
                apiKey=tsp.get_config()["api_key"],
                wmtsLayerName=None,
            ),
        )

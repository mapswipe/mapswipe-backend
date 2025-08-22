import logging
import typing

from pyfirebase_mapswipe import models as firebase_models

from apps.tutorial.models import Tutorial, TutorialScenarioPage, TutorialTask
from project_types.base import tutorial as base_tutorial

from .project import TileMapServiceProjectProperty

logger = logging.getLogger(__name__)


class TileMapServiceTutorialTaskProperty(base_tutorial.BaseTutorialTaskProperty):
    tile_x: int
    tile_y: int
    # FIXME(tnagorra): Do we save this or get zoom_level from project
    tile_z: int


class TileMapServiceBaseTutorial[
    ProjectPropertyVar: TileMapServiceProjectProperty,
    TaskPropertyVar: TileMapServiceTutorialTaskProperty,
](
    base_tutorial.BaseTutorial[
        ProjectPropertyVar,
        TaskPropertyVar,
    ],
):
    def __init__(self, tutorial: Tutorial):
        super().__init__(tutorial)

    @typing.override
    def get_task_sort_keys(self, existing_values: list[str]) -> list[str]:
        return [*existing_values, "project_type_specifics__tile_x", "project_type_specifics__tile_y"]

    @typing.override
    def get_task_specifics_for_firebase(
        self,
        task: TutorialTask,
        index: int,
    ) -> firebase_models.FbTileMapServiceTutorialTask:
        task_specifics = self.tutorial_task_property_class.model_validate(task.project_type_specifics)

        # FIXME(tnagorra): Add validation that scenario_page_number should start from 1

        i = index % 6

        task_x = 100 + (2 * task.scenario.scenario_page_number - 1)
        if i < 3:
            task_x += 0
        else:
            task_x += 1

        task_y = 131072
        if i in [0, 3]:
            task_y += 0
        elif i in [1, 4]:
            task_y += 1
        elif i in [2, 5]:
            task_y += 2

        return firebase_models.FbTileMapServiceTutorialTask(
            geometry="",
            groupId=self.get_tutorial_group_key(),
            projectId=self.tutorial.firebase_id,
            referenceAnswer=task.reference,
            screen=task.scenario.scenario_page_number,
            taskId_real=f"{task_specifics.tile_z}-{task_specifics.tile_x}-{task_specifics.tile_y}",
            taskX=task_x,
            taskY=task_y,
            taskId=f"{task_specifics.tile_z}-{task_x}-{task_y}",
        )

    @typing.override
    def get_group_specifics_for_firebase(self):
        scenarios_count = TutorialScenarioPage.objects.filter(tutorial_id=self.tutorial.pk).count()

        return firebase_models.FbTileMapServiceTutorialGroup(
            xMin=100,  # this will be always set to 100
            xMax=100 + (2 * scenarios_count) - 1,  # this depends on the number of screens/tasks to show
            yMin=131072,  # this is set to be at the equator
            yMax=131072 + 3 - 1,  # this is set to be at the equator
        )

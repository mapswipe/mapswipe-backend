import logging
import typing

from pyfirebase_mapswipe import models as firebase_models

from apps.tutorial.models import Tutorial, TutorialScenarioPage, TutorialTask
from project_types.base import tutorial as base_tutorial

from .project import TileMapServiceProjectProperty

logger = logging.getLogger(__name__)


def synthetic_tile_position(index: int, screen: int) -> tuple[int, int]:
    """Return the synthetic (taskX, taskY) for a tutorial tile.

    Each screen shows 6 tiles arranged in a 2x3 column-major block: the first 3
    cells fill the left column top-to-bottom, the next 3 fill the right column
    top-to-bottom. `index` is the 0-based cell position within the screen (values
    wrap every 6 via the modulo).
    """
    cell = index % 6
    task_x = 100 + (2 * screen - 1) + (0 if cell < 3 else 1)
    task_y = 131072 + (cell % 3)
    return task_x, task_y


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
        screen: int,
    ) -> firebase_models.FbTileMapServiceTutorialTask:
        task_specifics = self.tutorial_task_property_class.model_validate(task.project_type_specifics)

        # index is a 1-based global counter (see create_tasks_on_firebase);
        # convert to a 0-based cell position for this screen.
        task_x, task_y = synthetic_tile_position(index - 1, screen)

        return firebase_models.FbTileMapServiceTutorialTask(
            geometry="",
            groupId=self.get_tutorial_group_key(),
            projectId=self.tutorial.firebase_id,
            referenceAnswer=task.reference,
            taskPartitionIndex=task.task_partition_index,
            screen=screen,
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

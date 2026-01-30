from apps.tutorial.models import Tutorial
from project_types.tile_map_service.base import tutorial as tile_map_service_tutorial

from .project import LocateProjectProperty


class LocateTutorialTaskProperty(tile_map_service_tutorial.TileMapServiceTutorialTaskProperty): ...


# TODO(susilnem): Handle tutorial for locate project type


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

import logging

from apps.tutorial.project_types.base import tutorial as base_tutorial

logger = logging.getLogger(__name__)


class TileMapServiceTutorialTaskProperty(base_tutorial.BaseTutorialTaskProperty):
    tile_x: int
    tile_y: int
    tile_z: int

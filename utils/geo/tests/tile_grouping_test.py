import typing
from pathlib import Path

from main.config import Config
from main.tests import TestCase
from utils.geo.tile_grouping import extent_to_groups, get_geometry_from_file

BASE_DIR = Path(__file__).resolve().parent


class TestProjectQuery(TestCase):
    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_project_geometries_intersection(self):
        zoom = 18

        project_extent_file = Path(Config.BASE_DIR, "assets/fixtures/polygon_with_intersection.geojson")
        project_extent_file_json = get_geometry_from_file(str(project_extent_file))

        groups_with_overlaps = extent_to_groups(project_extent_file_json, zoom, 100)
        assert len(groups_with_overlaps) == 92

    def test_group_size(self):
        zoom = 18
        project_extent_file = Path(Config.BASE_DIR, "assets/fixtures/aoi.geojson")

        project_extent_file_json = get_geometry_from_file(str(project_extent_file))

        groups_dict = extent_to_groups(project_extent_file_json, zoom, 100)

        assert len(groups_dict) == 711

        for _, group in groups_dict.items():
            # check if height is 3
            y_group_size = int(group["yMax"]) - int(group["yMin"]) + 1
            assert y_group_size == 3

        for _, group in groups_dict.items():
            # check if group x size is of factor 2
            x_group_size = int(group["xMax"]) - int(group["xMin"]) + 1
            assert x_group_size % 2 == 0

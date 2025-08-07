import typing

from main.tests import TestCase
from utils.geo.tile_functions import (
    lat_long_zoom_to_pixel_coords,
    pixel_coords_zoom_to_lat_lon,
    tile_coords_and_zoom_to_quad_key,
)


class TestGeoUtils(TestCase):
    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_lat_long_zoom_to_pixel_coords(self):
        # Lat=0, Lon=0 at zoom=0 (whole world 256x256)
        p = lat_long_zoom_to_pixel_coords(0, 0, 0)
        assert p.x == 128
        assert p.y == 128

        # test with zoom level 1
        p = lat_long_zoom_to_pixel_coords(0, 0, 1)
        # At zoom 1, map is 512x512 pixels, middle is 256,256
        assert p.x == 256
        assert p.y == 256

        # test with zoom level 2
        p = lat_long_zoom_to_pixel_coords(0, 0, 2)
        assert p.x == 512
        assert p.y == 512

        # test with zoom level 2
        p = lat_long_zoom_to_pixel_coords(0, 0, 2)
        assert p.x == 512
        assert p.y == 512

        # test with zoom level 5
        p = lat_long_zoom_to_pixel_coords(0, 0, 5)
        assert p.x == 4096
        assert p.y == 4096

    def test_pixel_coords_zoom_to_lat_lon(self):
        # Center of the map at zoom 0
        lon, lat = pixel_coords_zoom_to_lat_lon(128, 128, 0)
        assert lon == 0.0
        assert lat == 0.0

        # Known point (London: 51.5074° N, 0.1278° W) — rough pixel reverse at zoom 2
        # First, find its approximate pixel coords for zoom 2 manually or from a map tool
        lon, lat = pixel_coords_zoom_to_lat_lon(512, 341.3333, 2)
        assert lon == 0
        assert lat == 51.32604237282497

    def test_tile_coords_and_zoom_to_quadKey(self):
        # test_zoom0
        # At zoom 0, only one tile: quadkey is empty
        assert not tile_coords_and_zoom_to_quad_key(0, 0, 0)

        # test_zoom1_top_left
        # Zoom 1, top-left tile
        assert tile_coords_and_zoom_to_quad_key(0, 0, 1) == "0"

        # test_zoom1_top_right
        # Zoom 1, top-right tile
        assert tile_coords_and_zoom_to_quad_key(1, 0, 1) == "1"

        # test_zoom1_bottom_left
        assert tile_coords_and_zoom_to_quad_key(0, 1, 1) == "2"

        # test_zoom1_bottom_right
        assert tile_coords_and_zoom_to_quad_key(1, 1, 1) == "3"

        # test_example_zoom3
        # Example from explanation
        assert tile_coords_and_zoom_to_quad_key(3, 5, 3) == "213"

        # test_max_zoom_sample
        # Arbitrary case at zoom 5
        assert tile_coords_and_zoom_to_quad_key(10, 12, 5) == "03210"

        # Zoom 22
        max_tile_22 = (2**22) - 1
        # Top-left
        assert tile_coords_and_zoom_to_quad_key(0, 0, 22) == "0" * 22
        # Bottom-right
        assert tile_coords_and_zoom_to_quad_key(max_tile_22, max_tile_22, 22) == "3" * 22

        # Zoom 23
        max_tile_23 = (2**23) - 1
        # Top-left
        assert tile_coords_and_zoom_to_quad_key(0, 0, 23) == "0" * 23
        # Bottom-right
        assert tile_coords_and_zoom_to_quad_key(max_tile_23, max_tile_23, 23) == "3" * 23

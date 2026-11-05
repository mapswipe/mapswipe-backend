import typing

import pydantic
import pytest

from main.tests import TestCase
from utils.geo.raster_tile_server.models import RasterTileServerConfig

BING_TILE_SERVER_PROPERTY: dict[str, typing.Any] = {"name": "BING", "bing": {"credits": "Bing credits"}}
CUSTOM_TILE_SERVER_PROPERTY: dict[str, typing.Any] = {
    "name": "CUSTOM",
    "custom": {
        "credits": "Custom credits",
        "url": "https://custom.example.com/{z}/{x}/{y}.png",
    },
}


def _with_zoom_range(tile_server_property: dict[str, typing.Any], **zoom_range: int) -> dict[str, typing.Any]:
    key = tile_server_property["name"].lower()
    return {**tile_server_property, key: {**tile_server_property[key], **zoom_range}}


class TestRasterTileServerZoomRange(TestCase):
    def test_zoom_range_is_optional(self):
        for tile_server_property in [BING_TILE_SERVER_PROPERTY, CUSTOM_TILE_SERVER_PROPERTY]:
            config = RasterTileServerConfig.model_validate(tile_server_property).get_config()
            assert config["min_zoom"] is None
            assert config["max_zoom"] is None

    def test_zoom_range_is_saved(self):
        for tile_server_property in [BING_TILE_SERVER_PROPERTY, CUSTOM_TILE_SERVER_PROPERTY]:
            for min_zoom, max_zoom in [(0, 0), (1, 19), (16, 24)]:
                config = RasterTileServerConfig.model_validate(
                    _with_zoom_range(tile_server_property, min_zoom=min_zoom, max_zoom=max_zoom),
                ).get_config()
                assert config["min_zoom"] == min_zoom
                assert config["max_zoom"] == max_zoom

    def test_inverted_zoom_range_is_rejected(self):
        for tile_server_property in [BING_TILE_SERVER_PROPERTY, CUSTOM_TILE_SERVER_PROPERTY]:
            with pytest.raises(pydantic.ValidationError, match="min zoom must not be greater than max zoom"):
                RasterTileServerConfig.model_validate(_with_zoom_range(tile_server_property, min_zoom=19, max_zoom=18))

    def test_negative_zoom_is_rejected(self):
        for tile_server_property in [BING_TILE_SERVER_PROPERTY, CUSTOM_TILE_SERVER_PROPERTY]:
            for zoom_range in [{"min_zoom": -1}, {"max_zoom": -1}]:
                with pytest.raises(pydantic.ValidationError):
                    RasterTileServerConfig.model_validate(_with_zoom_range(tile_server_property, **zoom_range))

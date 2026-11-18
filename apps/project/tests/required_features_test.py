import typing

from apps.common.models import AppFeatureEnum
from apps.project.models import Project, ProjectTypeEnum
from main.tests import TestCase
from project_types.store import get_project_type_handler

TILE_SERVER = {
    "name": "BING",
    "custom": None,
    "bing": {"credits": "My Map"},
    "mapbox": None,
    "maxar_standard": None,
    "maxar_premium": None,
    "esri": None,
    "esri_beta": None,
}

RASTER_OVERLAY = {
    "type": "RASTER_TILE",
    "vector": None,
    "raster": {"opacity": 1.0, "tile_server": TILE_SERVER},
}

VECTOR_OVERLAY = {
    "type": "VECTOR_TILE",
    "raster": None,
    "vector": {
        "tile_server": {
            "name": "CUSTOM",
            "custom": {
                "url": "https://custom-osm-data/{x}/{y}/{z}.pbf",
                "credits": "custom osm",
                "source_layer": "custom-source-name",
                "min_zoom": 0,
                "max_zoom": 14,
            },
            "openStreetMap": None,
            "openFreeMap": None,
            "versatiles": None,
        },
        "fill_color": "#ff00ff",
        "fill_opacity": 1.0,
        "line_color": "#ffff00",
        "line_opacity": 1.0,
        "line_width": 1.0,
        "line_dasharray": [1, 1],
        "circle_color": "#0000ff",
        "circle_opacity": 1.0,
        "circle_radius": 10.0,
    },
}


class TestRequiredFeatures(TestCase):
    @staticmethod
    def _get_required_features(overlay: dict[str, typing.Any]):
        project = Project(
            project_type=ProjectTypeEnum.COMPLETENESS,
            project_type_specifics={
                "zoom_level": 14,
                "aoi_geometry": "1",
                "tile_server_property": TILE_SERVER,
                "overlay_tile_server_property": overlay,
            },
        )
        return get_project_type_handler(ProjectTypeEnum.COMPLETENESS)(project).get_required_features()

    def test_completeness_project(self):
        assert self._get_required_features(RASTER_OVERLAY) == []
        assert self._get_required_features(VECTOR_OVERLAY) == [AppFeatureEnum.PROJECT_COMPLETENESS_VECTOR_LAYER]

    def test_feature_values_are_names(self):
        # NOTE: The values are stored in firebase and used by the clients, and GraphQL uses the names
        for feature in AppFeatureEnum:
            assert feature.value == feature.name

import typing

from django.db import models


class VectorTileServerNameEnum(models.TextChoices):
    CUSTOM = "CUSTOM", "Custom"
    OPEN_STREET_MAP = "OPEN_STREET_MAP", "Open Street Map"
    OPEN_FREE_MAP = "OPEN_FREE_MAP", "Open Free Map"
    VERSATILES = "VERSATILES", "Versatiles"


_VectorTileServerNameEnumWithoutCustom = typing.Literal[
    VectorTileServerNameEnum.OPEN_STREET_MAP,
    VectorTileServerNameEnum.OPEN_FREE_MAP,
    VectorTileServerNameEnum.VERSATILES,
]

assert {key for key, _ in VectorTileServerNameEnum.choices if key != VectorTileServerNameEnum.CUSTOM} == {
    enum.value for enum in typing.get_args(_VectorTileServerNameEnumWithoutCustom)
}, "Make sure _VectorTileServerNameEnumWithoutCustom includes all fields except CUSTOM from VectorTileServerNameEnum"


class VectorTileServerConfig(typing.TypedDict):
    url: str
    credits: str
    min_zoom: int
    max_zoom: int
    layers: list[str]


class VectorConfig:
    @staticmethod
    def get_config(name: _VectorTileServerNameEnumWithoutCustom) -> VectorTileServerConfig:
        match name:
            case VectorTileServerNameEnum.OPEN_STREET_MAP:
                # Style JSON: "https://vector.osm.org/demo/shortbread/colorful.json",
                return {
                    "url": "https://vector.osm.org/shortbread_v1/{z}/{x}/{y}.mvt",
                    "credits": "Map data from OpenStreetMap",
                    "min_zoom": 0,
                    "max_zoom": 14,
                    "layers": [
                        "buildings",
                        "boundaries",
                        "bridges",
                        "dam_lines",
                        "dam_polygons",
                        "ferries",
                        "land",
                        "ocean",
                        "pier_lines",
                        "pier_polygons",
                        "sites",
                        "street_polygons",
                        "streets",
                        "water_lines",
                        "water_polygons",
                    ],
                }
            case VectorTileServerNameEnum.OPEN_FREE_MAP:
                # TODO(tnagorra): The pbf URL might change every week so we need to make sure
                # Style JSON: "https://tiles.openfreemap.org/styles/liberty",
                return {
                    "url": "https://tiles.openfreemap.org/planet/20250528_001001_pt/{z}/{x}/{y}.pbf",
                    "credits": "OpenFreeMap © OpenMapTiles Data from OpenStreetMap",
                    "min_zoom": 0,
                    "max_zoom": 14,
                    "layers": [
                        "building",
                        "aeroway",
                        "boundary",
                        "landcover",
                        "landuse",
                        "park",
                        "transportation",
                        "water",
                        "waterway",
                    ],
                }
            case VectorTileServerNameEnum.VERSATILES:
                # Style JSON: "https://tiles.versatiles.org/assets/styles/colorful/style.json",
                return {
                    "url": "https://tiles.versatiles.org/tiles/osm/{z}/{x}/{y}",
                    "credits": "Map data from OpenStreetMap",
                    "min_zoom": 0,
                    "max_zoom": 14,
                    "layers": [
                        "buildings",
                        "boundaries",
                        "bridges",
                        "dam_lines",
                        "dam_polygons",
                        "ferries",
                        "land",
                        "ocean",
                        "pier_lines",
                        "pier_polygons",
                        "sites",
                        "street_polygons",
                        "streets",
                        "water_lines",
                        "water_polygons",
                    ],
                }

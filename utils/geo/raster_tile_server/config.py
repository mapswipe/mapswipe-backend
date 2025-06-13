import typing

from django.conf import settings
from django.db import models


class RasterTileServerNameEnum(models.TextChoices):
    CUSTOM = "CUSTOM", "Custom"
    BING = "BING", "Bing"
    MAPBOX = "MAPBOX", "Mapbox"
    MAXAR_STANDARD = "MAXAR_STANDARD", "Maxar Standard"
    MAXAR_PREMIUM = "MAXAR_PREMIUM", "Maxar Premium"
    ESRI = "ESRI", "ESRI World Imagery"
    ESRI_BETA = "ESRI_BETA", "ESRI World Imagery (Clarity) Beta"


_RasterTileServerNameEnumWithoutCustom = typing.Literal[
    RasterTileServerNameEnum.BING,
    RasterTileServerNameEnum.MAPBOX,
    RasterTileServerNameEnum.MAXAR_STANDARD,
    RasterTileServerNameEnum.MAXAR_PREMIUM,
    RasterTileServerNameEnum.ESRI,
    RasterTileServerNameEnum.ESRI_BETA,
]

assert {key for key, _ in RasterTileServerNameEnum.choices if key != RasterTileServerNameEnum.CUSTOM} == {
    enum.value for enum in typing.get_args(_RasterTileServerNameEnumWithoutCustom)
}, "Make sure _RasterTileServerNameEnumWithoutCustom includes all fields except CUSTOM from RasterTileServerNameEnum"


class RasterTileServerConfig(typing.TypedDict):
    url: str
    credits: str


class RasterConfig:
    @staticmethod
    def get_config(name: _RasterTileServerNameEnumWithoutCustom) -> RasterTileServerConfig:
        match name:
            case RasterTileServerNameEnum.BING:
                return {
                    "url": (
                        "https://ecn.t0.tiles.virtualearth.net"
                        "/tiles/a{quadkey}.jpeg"
                        f"?g=7505&token={settings.MAP_IMAGE_BING_API_KEY}"
                    ),
                    "credits": "© 2019 Microsoft Corporation, Earthstar Geographics SIO",
                }
            case RasterTileServerNameEnum.MAPBOX:
                return {
                    "url": (
                        "https://d.tiles.mapbox.com"
                        "/v4/mapbox.satellite"
                        "/{z}/{x}/{y}.jpg"
                        f"?access_token={settings.MAP_IMAGE_MAPBOX_API_KEY}"
                    ),
                    "credits": "© 2019 MapBox",
                }
            case RasterTileServerNameEnum.MAXAR_PREMIUM:
                return {
                    "url": (
                        "https://services.digitalglobe.com"
                        "/earthservice/tmsaccess/tms/1.0.0/DigitalGlobe%3AImageryTileService@EPSG%3A3857@jpg"
                        "/{z}/{x}/{y}.jpg"
                        f"?connectId={settings.MAP_IMAGE_MAXAR_PREMIUM_API_KEY}"
                    ),
                    "credits": "© 2019 Maxar",
                }
            case RasterTileServerNameEnum.MAXAR_STANDARD:
                return {
                    "url": (
                        "https://services.digitalglobe.com"
                        "/earthservice/tmsaccess/tms/1.0.0/DigitalGlobe%3AImageryTileService@EPSG%3A3857@jpg"
                        "/{z}/{x}/{y}.jpg"
                        f"?connectId={settings.MAP_IMAGE_MAXAR_STANDARD_API_KEY}"
                    ),
                    "credits": "© 2019 Maxar",
                }
            case RasterTileServerNameEnum.ESRI:
                return {
                    "url": (
                        "https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                    ),
                    "credits": "© 2019 ESRI",
                }
            case RasterTileServerNameEnum.ESRI_BETA:
                return {
                    "url": (
                        "https://clarity.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                    ),
                    "credits": "© 2019 ESRI",
                }

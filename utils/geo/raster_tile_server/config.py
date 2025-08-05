import typing

from django.conf import settings
from django.db import models
from pyfirebase_mapswipe import models as firebase_models


class RasterTileServerNameEnum(models.TextChoices):
    CUSTOM = "CUSTOM", "Custom"
    BING = "BING", "Bing"
    MAPBOX = "MAPBOX", "Mapbox"
    MAXAR_STANDARD = "MAXAR_STANDARD", "Maxar Standard"
    MAXAR_PREMIUM = "MAXAR_PREMIUM", "Maxar Premium"
    ESRI = "ESRI", "ESRI World Imagery"
    ESRI_BETA = "ESRI_BETA", "ESRI World Imagery (Clarity) Beta"

    def to_firebase(self) -> firebase_models.FbEnumRasterTileServerName:
        match self:
            case RasterTileServerNameEnum.CUSTOM:
                return firebase_models.FbEnumRasterTileServerName.CUSTOM
            case RasterTileServerNameEnum.BING:
                return firebase_models.FbEnumRasterTileServerName.BING
            case RasterTileServerNameEnum.MAPBOX:
                return firebase_models.FbEnumRasterTileServerName.MAPBOX
            case RasterTileServerNameEnum.MAXAR_STANDARD:
                return firebase_models.FbEnumRasterTileServerName.MAXAR_STANDARD
            case RasterTileServerNameEnum.MAXAR_PREMIUM:
                return firebase_models.FbEnumRasterTileServerName.MAXAR_PREMIUM
            case RasterTileServerNameEnum.ESRI:
                return firebase_models.FbEnumRasterTileServerName.ESRI
            case RasterTileServerNameEnum.ESRI_BETA:
                return firebase_models.FbEnumRasterTileServerName.ESRI_BETA


RasterTileServerNameEnumWithoutCustom = typing.Literal[
    RasterTileServerNameEnum.BING,
    RasterTileServerNameEnum.MAPBOX,
    RasterTileServerNameEnum.MAXAR_STANDARD,
    RasterTileServerNameEnum.MAXAR_PREMIUM,
    RasterTileServerNameEnum.ESRI,
    RasterTileServerNameEnum.ESRI_BETA,
]

assert {key for key, _ in RasterTileServerNameEnum.choices if key != RasterTileServerNameEnum.CUSTOM} == {
    enum.value for enum in typing.get_args(RasterTileServerNameEnumWithoutCustom)
}, "Make sure RasterTileServerNameEnumWithoutCustom includes all fields except CUSTOM from RasterTileServerNameEnum"


class RasterTileServerNormConfig(typing.TypedDict):
    url: str
    raw_url: str
    api_key: str
    credits: str


class RasterConfig:
    @staticmethod
    def get_config(name: RasterTileServerNameEnumWithoutCustom) -> RasterTileServerNormConfig:
        match name:
            case RasterTileServerNameEnum.BING:
                api_key = settings.MAP_IMAGE_BING_API_KEY
                url = "https://ecn.t0.tiles.virtualearth.net/tiles/a{{quadkey}}.jpeg?g=7505&token={apiKey}"
                return {
                    "url": url.format(apiKey=api_key),
                    "raw_url": url.format(apiKey="{apiKey}"),
                    "api_key": api_key,
                    "credits": "© 2019 Microsoft Corporation, Earthstar Geographics SIO",
                }
            case RasterTileServerNameEnum.MAPBOX:
                api_key = settings.MAP_IMAGE_MAPBOX_API_KEY
                url = "https://d.tiles.mapbox.com/v4/mapbox.satellite/{{z}}/{{x}}/{{y}}.jpg?access_token={apiKey}"
                return {
                    "url": url.format(apiKey=api_key),
                    "raw_url": url.format(apiKey="{apiKey}"),
                    "api_key": api_key,
                    "credits": "© 2019 MapBox",
                }
            case RasterTileServerNameEnum.MAXAR_PREMIUM:
                api_key = settings.MAP_IMAGE_MAXAR_PREMIUM_API_KEY
                url = (
                    "https://services.digitalglobe.com"
                    "/earthservice/tmsaccess/tms/1.0.0/DigitalGlobe%3AImageryTileService@EPSG%3A3857@jpg"
                    "/{{z}}/{{x}}/{{y}}.jpg"
                    "?connectId={apiKey}"
                )
                return {
                    "url": url.format(apiKey=api_key),
                    "raw_url": url.format(apiKey="{apiKey}"),
                    "api_key": api_key,
                    "credits": "© 2019 Maxar",
                }
            case RasterTileServerNameEnum.MAXAR_STANDARD:
                api_key = settings.MAP_IMAGE_MAXAR_STANDARD_API_KEY
                url = (
                    "https://services.digitalglobe.com"
                    "/earthservice/tmsaccess/tms/1.0.0/DigitalGlobe%3AImageryTileService@EPSG%3A3857@jpg"
                    "/{{z}}/{{x}}/{{y}}.jpg"
                    "?connectId={apiKey}"
                )
                return {
                    "url": url.format(apiKey=api_key),
                    "raw_url": url.format(apiKey="{apiKey}"),
                    "api_key": api_key,
                    "credits": "© 2019 Maxar",
                }
            case RasterTileServerNameEnum.ESRI:
                url = "https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                return {
                    "url": url,
                    "raw_url": url,
                    "api_key": "",
                    "credits": "© 2019 ESRI",
                }
            case RasterTileServerNameEnum.ESRI_BETA:
                url = "https://clarity.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                return {
                    "url": url,
                    "raw_url": url,
                    "api_key": "",
                    "credits": "© 2019 ESRI",
                }

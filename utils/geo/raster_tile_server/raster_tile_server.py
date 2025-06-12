import math
import typing
from abc import ABC

from django.core.exceptions import ValidationError

from utils.common import validate_imagery_url
from utils.geo.tile_functions import tile_coords_and_zoom_to_quadKey

from .config import Config, RasterTileServerNameEnum
from .models import (
    RasterTileServerCommonConfig,
    RasterTileServerConfig,
    RasterTileServerCustomConfig,
)


class BaseVectorTileServerException(Exception): ...


class _BaseRasterTileServer(ABC):
    """Create a tile server class."""

    name: RasterTileServerNameEnum
    url: str
    api_key: str
    credits: str | None

    # FIXME(tnagorra): We might need to move this to pydantic object
    @staticmethod
    def check_imagery_url(url: str) -> bool:
        try:
            validate_imagery_url(url, support_quadkey=True)
            return True
        except ValidationError as e:
            raise BaseVectorTileServerException(e.message) from e

    def generate_url(self, tile_x: int, tile_y: int, tile_z: int) -> str:
        return self.url.format(
            key=self.api_key,
            x=tile_x,
            y=tile_y,
            z=tile_z,
        )


class CustomRasterTileServer(_BaseRasterTileServer):
    name = RasterTileServerNameEnum.CUSTOM

    def __init__(
        self,
        config: RasterTileServerCustomConfig,
    ):
        self.url = config.url
        self.credits = config.credits
        self.check_imagery_url(self.url)

    @typing.override
    def generate_url(self, tile_x: int, tile_y: int, tile_z: int) -> str:
        # TODO(tnagorra): We might need to add support for quadkey for custom tile servers
        return self.url.format(
            x=tile_x,
            y=tile_y,
            z=tile_z,
        )


class _CommonRasterTileServer(_BaseRasterTileServer):
    def __init__(
        self,
        config: RasterTileServerCommonConfig,
    ):
        self.credits = config.credits

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.check_imagery_url(cls.url)
        if getattr(cls, "name", None) is None:
            raise NotImplementedError(f"Please define name for {cls}")
        if getattr(cls, "api_key", None) is None:
            raise NotImplementedError(f"Please define api_key for {cls}")
        if getattr(cls, "url", None) is None:
            raise NotImplementedError(f"Please define url for {cls}")


class BingRasterTileServer(_CommonRasterTileServer):
    name = RasterTileServerNameEnum.BING
    url = Config.IMAGE_URLS[RasterTileServerNameEnum.BING]
    api_key = Config.IMAGE_API_KEYS[RasterTileServerNameEnum.BING]

    @typing.override
    def generate_url(self, tile_x: int, tile_y: int, tile_z: int) -> str:
        quadkey = tile_coords_and_zoom_to_quadKey(tile_x, tile_y, tile_z)
        return self.url.format(
            key=self.api_key,
            quadkey=quadkey,
        )


class MapboxRasterTileServer(_CommonRasterTileServer):
    name = RasterTileServerNameEnum.MAPBOX
    url = Config.IMAGE_URLS[RasterTileServerNameEnum.MAPBOX]
    api_key = Config.IMAGE_API_KEYS[RasterTileServerNameEnum.MAPBOX]


class MaxarStandardRasterTileServer(_CommonRasterTileServer):
    name = RasterTileServerNameEnum.MAXAR_STANDARD
    url = Config.IMAGE_URLS[RasterTileServerNameEnum.MAXAR_STANDARD]
    api_key = Config.IMAGE_API_KEYS[RasterTileServerNameEnum.MAXAR_STANDARD]

    @typing.override
    def generate_url(self, tile_x: int, tile_y: int, tile_z: int) -> str:
        # maxar uses not the standard TMS tile y coordinate,
        # but the Google tile y coordinate
        # more information here:
        # https://www.maptiler.com/google-maps-coordinates-tile-bounds-projection/
        tile_y = int(math.pow(2, tile_z) - tile_y) - 1
        return self.url.format(
            key=self.api_key,
            x=tile_x,
            y=tile_y,
            z=tile_z,
        )


class MaxarPremiumRasterTileServer(MaxarStandardRasterTileServer):
    name = RasterTileServerNameEnum.MAXAR_PREMIUM
    url = Config.IMAGE_URLS[RasterTileServerNameEnum.MAXAR_PREMIUM]
    api_key = Config.IMAGE_API_KEYS[RasterTileServerNameEnum.MAXAR_PREMIUM]


class EsriRasterTileServer(_CommonRasterTileServer):
    name = RasterTileServerNameEnum.ESRI
    url = Config.IMAGE_URLS[RasterTileServerNameEnum.ESRI]
    api_key = Config.IMAGE_API_KEYS[RasterTileServerNameEnum.ESRI]


class EsriBetaRasterTileServer(EsriRasterTileServer):
    name = RasterTileServerNameEnum.ESRI_BETA
    url = Config.IMAGE_URLS[RasterTileServerNameEnum.ESRI_BETA]
    api_key = Config.IMAGE_API_KEYS[RasterTileServerNameEnum.ESRI_BETA]


type AvailableRasterTileServerTypeAlias = (
    CustomRasterTileServer
    | BingRasterTileServer
    | MapboxRasterTileServer
    | MaxarStandardRasterTileServer
    | MaxarPremiumRasterTileServer
    | EsriRasterTileServer
    | EsriBetaRasterTileServer
)


def get_raster_tile_server(config: RasterTileServerConfig) -> AvailableRasterTileServerTypeAlias:
    match config.name:
        # Custom
        case RasterTileServerNameEnum.CUSTOM:
            assert config.custom is not None, "config.custom should be not none"
            return CustomRasterTileServer(config.custom)
        # Pre-defined
        case RasterTileServerNameEnum.BING:
            assert config.bing is not None, "config.bing should be not none"
            return BingRasterTileServer(config.bing)
        case RasterTileServerNameEnum.MAPBOX:
            assert config.mapbox is not None, "config.mapbox should be not none"
            return MapboxRasterTileServer(config.mapbox)
        case RasterTileServerNameEnum.MAXAR_STANDARD:
            assert config.maxar_standard is not None, "config.maxar_standard should be not none"
            return MaxarStandardRasterTileServer(config.maxar_standard)
        case RasterTileServerNameEnum.MAXAR_PREMIUM:
            assert config.maxar_premium is not None, "config.maxar_premium should be not none"
            return MaxarPremiumRasterTileServer(config.maxar_premium)
        case RasterTileServerNameEnum.ESRI:
            assert config.esri is not None, "config.esri should be not none"
            return EsriRasterTileServer(config.esri)
        case RasterTileServerNameEnum.ESRI_BETA:
            assert config.esri_beta is not None, "config.esri_beta should be not none"
            return EsriBetaRasterTileServer(config.esri_beta)

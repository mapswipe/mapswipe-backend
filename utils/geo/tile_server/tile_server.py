import math
import typing
from abc import ABC

from utils.geo.tile_functions import tile_coords_and_zoom_to_quadKey

from .config import Config, TileServerNameEnum
from .models import TileServerCommonConfig, TileServerConfig, TileServerCustomConfig


class BaseTileServerException(Exception): ...


class BaseTileServer(ABC):
    """Create a tile server class."""

    name: TileServerNameEnum
    url: str
    api_key: str
    credits: str | None

    @staticmethod
    def check_imagery_url(url: str) -> bool:
        """Check if imagery url contains xyz or quad key placeholders."""
        if all([substring in url for substring in ["{x}", "{y}", "{z}"]]) and not any(
            [substring in url for substring in ["{{x}}", "{{y}}", "{{z}}"]],
        ):
            return True
        if all([substring in url for substring in ["{x}", "{-y}", "{z}"]]) and not any(
            [substring in url for substring in ["{{x}}", "{{-y}}", "{{z}}"]],
        ):
            return True
        if "{quad_key}" in url and "{{quad_key}}" not in url:
            return True
        raise BaseTileServerException(
            f"The imagery url {url} must contain {{x}}, {{y}} (or {{-y}}) and {{{{z}}}} or the {{quad_key}} placeholders.",
        )

    def generate_url(self, tile_x: int, tile_y: int, tile_z: int) -> str:
        return self.url.format(
            key=self.api_key,
            x=tile_x,
            y=tile_y,
            z=tile_z,
        )


class CustomTileServer(BaseTileServer):
    name = TileServerNameEnum.CUSTOM

    def __init__(
        self,
        config: TileServerCustomConfig,
    ):
        self.url = config.url
        self.credits = config.credits
        self.check_imagery_url(self.url)

    @typing.override
    def generate_url(self, tile_x: int, tile_y: int, tile_z: int) -> str:
        # FIXME: We might need to add support for quad_key for custom tile servers
        return self.url.format(
            x=tile_x,
            y=tile_y,
            z=tile_z,
        )


class CommonTileServer(BaseTileServer):
    def __init__(
        self,
        config: TileServerCommonConfig,
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


class BingTileServer(CommonTileServer):
    name = TileServerNameEnum.BING
    url = Config.IMAGE_URLS[TileServerNameEnum.BING]
    api_key = Config.IMAGE_API_KEYS[TileServerNameEnum.BING]

    @typing.override
    def generate_url(self, tile_x: int, tile_y: int, tile_z: int) -> str:
        quadKey = tile_coords_and_zoom_to_quadKey(tile_x, tile_y, tile_z)
        return self.url.format(
            key=self.api_key,
            quadKey=quadKey,
        )


class MapboxTileServer(CommonTileServer):
    name = TileServerNameEnum.MAPBOX
    url = Config.IMAGE_URLS[TileServerNameEnum.MAPBOX]
    api_key = Config.IMAGE_API_KEYS[TileServerNameEnum.MAPBOX]


class MaxarStandardTileServer(CommonTileServer):
    name = TileServerNameEnum.MAXAR_STANDARD
    url = Config.IMAGE_URLS[TileServerNameEnum.MAXAR_STANDARD]
    api_key = Config.IMAGE_API_KEYS[TileServerNameEnum.MAXAR_STANDARD]

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


class MaxarPremiumTileServer(MaxarStandardTileServer):
    name = TileServerNameEnum.MAXAR_PREMIUM
    url = Config.IMAGE_URLS[TileServerNameEnum.MAXAR_PREMIUM]
    api_key = Config.IMAGE_API_KEYS[TileServerNameEnum.MAXAR_PREMIUM]


class EsriTileServer(CommonTileServer):
    name = TileServerNameEnum.ESRI
    url = Config.IMAGE_URLS[TileServerNameEnum.ESRI]
    api_key = Config.IMAGE_API_KEYS[TileServerNameEnum.ESRI]


class EsriBetaTileServer(EsriTileServer):
    name = TileServerNameEnum.ESRI_BETA
    url = Config.IMAGE_URLS[TileServerNameEnum.ESRI_BETA]
    api_key = Config.IMAGE_API_KEYS[TileServerNameEnum.ESRI_BETA]


type AvailableTileServerTypeAlias = (
    CustomTileServer
    | BingTileServer
    | MapboxTileServer
    | MaxarStandardTileServer
    | MaxarPremiumTileServer
    | EsriTileServer
    | EsriBetaTileServer
)


def get_tile_server(config: TileServerConfig) -> AvailableTileServerTypeAlias:
    match config.name:
        # Custom
        case TileServerNameEnum.CUSTOM:
            assert config.custom is not None, "config.custom should be not none"
            return CustomTileServer(config.custom)
        # Pre-defined
        case TileServerNameEnum.BING:
            assert config.bing is not None, "config.bing should be not none"
            return BingTileServer(config.bing)
        case TileServerNameEnum.MAPBOX:
            assert config.mapbox is not None, "config.mapbox should be not none"
            return MapboxTileServer(config.mapbox)
        case TileServerNameEnum.MAXAR_STANDARD:
            assert config.maxar_standard is not None, "config.maxar_standard should be not none"
            return MaxarStandardTileServer(config.maxar_standard)
        case TileServerNameEnum.MAXAR_PREMIUM:
            assert config.maxar_premium is not None, "config.maxar_premium should be not none"
            return MaxarPremiumTileServer(config.maxar_premium)
        case TileServerNameEnum.ESRI:
            assert config.esri is not None, "config.esri should be not none"
            return EsriTileServer(config.esri)
        case TileServerNameEnum.ESRI_BETA:
            assert config.esri_beta is not None, "config.esri_beta should be not none"
            return EsriBetaTileServer(config.esri_beta)

import math
import typing
from abc import ABC

from utils.geo.tile_functions import tile_coords_and_zoom_to_quadKey

from .config import Config, TileServerName
from .models import CommonTileServerConfig, CustomTileServerConfig, TileServerConfigAlias


class BaseTileServerException(Exception): ...


CUSTOM_TILE_SERVER = "custom"


def get_api_key(name: TileServerName) -> str | None:
    if name == CUSTOM_TILE_SERVER:
        return None
    return Config.IMAGE_API_KEYS[name]


def get_tile_server_url(name: TileServerName) -> str | None:
    if name == CUSTOM_TILE_SERVER:
        return None
    return Config.IMAGE_URLS[name]


class BaseTileServer(ABC):
    """Create a tile server class."""

    name: TileServerName
    url: str
    api_key: str
    credits: str | None

    @staticmethod
    def check_imagery_url(url: str) -> bool:
        """Check if imagery url contains xyz or quad key placeholders."""
        if all([substring in url for substring in ["{x}", "{y}", "{z}"]]):
            return True
        elif all([substring in url for substring in ["{x}", "{-y}", "{z}"]]):
            return True
        elif "{quad_key}" in url:
            return True
        raise BaseTileServerException(
            f"The imagery url {url} must contain {{x}}, {{y}} (or {{-y}}) and {{{{z}}}} or the {{quad_key}} placeholders."
        )

    @classmethod
    def generate_url(cls, tile_x: int, tile_y: int, tile_z: int) -> str:
        return cls.url.format(
            key=cls.api_key,
            x=tile_x,
            y=tile_y,
            z=tile_z,
        )


class CustomTileServer(BaseTileServer):
    name = TileServerName.CUSTOM

    def __init__(
        self,
        config: CustomTileServerConfig,
    ):
        self.url = config.url
        self.credits = config.credits
        self.check_imagery_url(self.url)

    @classmethod
    def generate_url(cls, tile_x: int, tile_y: int, tile_z: int) -> str:
        return cls.url.format(
            x=tile_x,
            y=tile_y,
            z=tile_z,
        )


class CommonTileServer(BaseTileServer):
    def __init__(
        self,
        config: CommonTileServerConfig,
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
    name = TileServerName.BING
    url = Config.IMAGE_URLS[TileServerName.BING]
    api_key = Config.IMAGE_API_KEYS[TileServerName.BING]

    @classmethod
    def generate_url(cls, tile_x: int, tile_y: int, tile_z: int) -> str:
        quadKey = tile_coords_and_zoom_to_quadKey(tile_x, tile_y, tile_z)
        return "https://ecn.t0.tiles.virtualearth.net/tiles/a{}.jpeg?g=7505&mkt=en-US&token={}".format(
            quadKey,
            cls.api_key,
        )


class MapboxTileServer(CommonTileServer):
    name = TileServerName.MAPBOX
    url = Config.IMAGE_URLS[TileServerName.MAPBOX]
    api_key = Config.IMAGE_API_KEYS[TileServerName.MAPBOX]


class MaxarStandardTileServer(CommonTileServer):
    name = TileServerName.MAXAR_STANDARD
    url = Config.IMAGE_URLS[TileServerName.MAXAR_STANDARD]
    api_key = Config.IMAGE_API_KEYS[TileServerName.MAXAR_STANDARD]

    @classmethod
    def generate_url(cls, tile_x: int, tile_y: int, tile_z: int) -> str:
        # maxar uses not the standard TMS tile y coordinate,
        # but the Google tile y coordinate
        # more information here:
        # https://www.maptiler.com/google-maps-coordinates-tile-bounds-projection/
        tile_y = int(math.pow(2, tile_z) - tile_y) - 1
        return cls.url.format(
            key=cls.api_key,
            x=tile_x,
            y=tile_y,
            z=tile_z,
        )


class MaxarPremiumTileServer(MaxarStandardTileServer):
    name = TileServerName.MAXAR_PREMIUM
    url = Config.IMAGE_URLS[TileServerName.MAXAR_PREMIUM]
    api_key = Config.IMAGE_API_KEYS[TileServerName.MAXAR_PREMIUM]


class EsriTileServer(CommonTileServer):
    name = TileServerName.ESRI
    url = Config.IMAGE_URLS[TileServerName.ESRI]
    api_key = Config.IMAGE_API_KEYS[TileServerName.ESRI]


class EsriBetaTileServer(EsriTileServer):
    name = TileServerName.ESRI_BETA
    url = Config.IMAGE_URLS[TileServerName.ESRI_BETA]
    api_key = Config.IMAGE_API_KEYS[TileServerName.ESRI_BETA]


AvailableTileServerNameTypeAlias: typing.TypeAlias = typing.Literal[
    TileServerName.BING,
    TileServerName.MAPBOX,
    TileServerName.MAXAR_STANDARD,
    TileServerName.MAXAR_PREMIUM,
    TileServerName.ESRI,
    TileServerName.ESRI_BETA,
]

AvailableTileServerTypeAlias: typing.TypeAlias = (
    CustomTileServer
    | BingTileServer
    | MapboxTileServer
    | MaxarStandardTileServer
    | MaxarPremiumTileServer
    | EsriTileServer
    | EsriBetaTileServer
)


def get_tile_server_type(server_name: TileServerName) -> type[AvailableTileServerTypeAlias | CustomTileServer]:
    if server_name == TileServerName.BING:
        return BingTileServer
    elif server_name == TileServerName.MAPBOX:
        return MapboxTileServer
    elif server_name == TileServerName.MAXAR_STANDARD:
        return MaxarStandardTileServer
    elif server_name == TileServerName.MAXAR_PREMIUM:
        return MaxarPremiumTileServer
    elif server_name == TileServerName.ESRI:
        return EsriTileServer
    elif server_name == TileServerName.ESRI_BETA:
        return EsriBetaTileServer
    elif server_name == TileServerName.CUSTOM:
        return CustomTileServer


def get_tile_server(config: TileServerConfigAlias) -> AvailableTileServerTypeAlias | CustomTileServer:
    server_type = get_tile_server_type(config.name)
    return server_type(config)  # type: ignore[reportArgumentType]

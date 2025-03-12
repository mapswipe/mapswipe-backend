import math
import typing
from abc import ABC

from utils.geo.tile_functions import tile_coords_and_zoom_to_quadKey

from .config import Config, TileServerNameEnum
from .models import CommonTileServerConfig, CustomTileServerConfig, TileServerConfigAlias


class BaseTileServerException(Exception): ...


CUSTOM_TILE_SERVER = "custom"


def get_api_key(name: TileServerNameEnum) -> str | None:
    if name == CUSTOM_TILE_SERVER:
        return None
    return Config.IMAGE_API_KEYS[name]


def get_tile_server_url(name: TileServerNameEnum) -> str | None:
    if name == CUSTOM_TILE_SERVER:
        return None
    return Config.IMAGE_URLS[name]


class BaseTileServer(ABC):
    """Create a tile server class."""

    name: TileServerNameEnum
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
    name = TileServerNameEnum.CUSTOM

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
    name = TileServerNameEnum.BING
    url = Config.IMAGE_URLS[TileServerNameEnum.BING]
    api_key = Config.IMAGE_API_KEYS[TileServerNameEnum.BING]

    @classmethod
    def generate_url(cls, tile_x: int, tile_y: int, tile_z: int) -> str:
        quadKey = tile_coords_and_zoom_to_quadKey(tile_x, tile_y, tile_z)
        return "https://ecn.t0.tiles.virtualearth.net/tiles/a{}.jpeg?g=7505&mkt=en-US&token={}".format(
            quadKey,
            cls.api_key,
        )


class MapboxTileServer(CommonTileServer):
    name = TileServerNameEnum.MAPBOX
    url = Config.IMAGE_URLS[TileServerNameEnum.MAPBOX]
    api_key = Config.IMAGE_API_KEYS[TileServerNameEnum.MAPBOX]


class MaxarStandardTileServer(CommonTileServer):
    name = TileServerNameEnum.MAXAR_STANDARD
    url = Config.IMAGE_URLS[TileServerNameEnum.MAXAR_STANDARD]
    api_key = Config.IMAGE_API_KEYS[TileServerNameEnum.MAXAR_STANDARD]

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


AvailableTileServerNameTypeAlias: typing.TypeAlias = typing.Literal[
    TileServerNameEnum.BING,
    TileServerNameEnum.MAPBOX,
    TileServerNameEnum.MAXAR_STANDARD,
    TileServerNameEnum.MAXAR_PREMIUM,
    TileServerNameEnum.ESRI,
    TileServerNameEnum.ESRI_BETA,
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


def get_tile_server_type(server_name: TileServerNameEnum) -> type[AvailableTileServerTypeAlias | CustomTileServer]:
    if server_name == TileServerNameEnum.BING:
        return BingTileServer
    elif server_name == TileServerNameEnum.MAPBOX:
        return MapboxTileServer
    elif server_name == TileServerNameEnum.MAXAR_STANDARD:
        return MaxarStandardTileServer
    elif server_name == TileServerNameEnum.MAXAR_PREMIUM:
        return MaxarPremiumTileServer
    elif server_name == TileServerNameEnum.ESRI:
        return EsriTileServer
    elif server_name == TileServerNameEnum.ESRI_BETA:
        return EsriBetaTileServer
    elif server_name == TileServerNameEnum.CUSTOM:
        return CustomTileServer


def get_tile_server(config: TileServerConfigAlias) -> AvailableTileServerTypeAlias | CustomTileServer:
    server_type = get_tile_server_type(config.name)
    return server_type(config)  # type: ignore[reportArgumentType]

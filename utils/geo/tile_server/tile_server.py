import math
import typing
from abc import ABC

from utils.geo.tile_functions import tile_coords_and_zoom_to_quadKey

from .config import Config, TileServerNameEnum, VectorTileServerNameEnum
from .models import (
    TileServerCommonConfig,
    TileServerConfig,
    TileServerCustomConfig,
    VectorTileServerCommonConfig,
    VectorTileServerConfig,
    VectorTileServerCustomConfig,
)


class BaseTileServerException(Exception): ...


class BaseTileServer(ABC):
    """Create a tile server class."""

    name: TileServerNameEnum
    url: str
    api_key: str
    credits: str | None

    # FIXME(tnagorra): We might need to move this to pydantic object
    # FIXME(tnagorra): We should not support {{x}} syntax as we will be using maplibre
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
        if "{quadkey}" in url and "{{quadkey}}" not in url:
            return True
        raise BaseTileServerException(
            f"The imagery url {url} must contain {{x}}, {{y}} (or {{-y}}) and {{z}} or the {{quadkey}} placeholders.",
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
        # TODO(tnagorra): We might need to add support for quadkey for custom tile servers
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
        quadkey = tile_coords_and_zoom_to_quadKey(tile_x, tile_y, tile_z)
        return self.url.format(
            key=self.api_key,
            quadkey=quadkey,
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


class BaseVectorTileServer(ABC):
    """Create a tile server class."""

    type: VectorTileServerNameEnum
    url: str
    source_name: str
    credits: str | None

    # FIXME(tnagorra): We might need to move this to pydantic object
    # FIXME(tnagorra): We should not support {{x}} syntax as we will be using maplibre
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
        raise BaseTileServerException(
            f"The imagery url {url} must contain {{x}}, {{y}} (or {{-y}}) and {{z}} placeholders.",
        )


class CustomVectorTileServer(BaseVectorTileServer):
    type = VectorTileServerNameEnum.CUSTOM

    def __init__(
        self,
        config: VectorTileServerCustomConfig,
    ):
        self.url = config.url
        self.source_name = config.source_name
        self.credits = config.credits


class OpenStreetMapVectorTileServer(BaseVectorTileServer):
    type = VectorTileServerNameEnum.OPEN_STREET_MAP
    url = Config.VECTOR_IMAGE_URLS[VectorTileServerNameEnum.OPEN_STREET_MAP]

    def __init__(
        self,
        config: VectorTileServerCommonConfig,
    ):
        self.source_name = config.source_name
        self.credits = config.credits


class OpenFreeMapVectorTileServer(BaseVectorTileServer):
    type = VectorTileServerNameEnum.OPEN_FREE_MAP
    url = Config.VECTOR_IMAGE_URLS[VectorTileServerNameEnum.OPEN_FREE_MAP]

    def __init__(
        self,
        config: VectorTileServerCommonConfig,
    ):
        self.source_name = config.source_name
        self.credits = config.credits


class VersatilesVectorTileServer(BaseVectorTileServer):
    type = VectorTileServerNameEnum.VERSATILES
    url = Config.VECTOR_IMAGE_URLS[VectorTileServerNameEnum.VERSATILES]

    def __init__(
        self,
        config: VectorTileServerCommonConfig,
    ):
        self.source_name = config.source_name
        self.credits = config.credits


type AvailableVectorTileServerTypeAlias = (
    CustomVectorTileServer | OpenStreetMapVectorTileServer | OpenFreeMapVectorTileServer | VersatilesVectorTileServer
)


def get_vector_tile_server(config: VectorTileServerConfig) -> AvailableVectorTileServerTypeAlias:
    match config.name:
        # Custom
        case VectorTileServerNameEnum.CUSTOM:
            assert config.custom is not None, "config.custom should be not none"
            return CustomVectorTileServer(config.custom)
        # Pre-defined
        case VectorTileServerNameEnum.OPEN_STREET_MAP:
            assert config.open_street_map is not None, "config.open_street_map should be not none"
            return OpenStreetMapVectorTileServer(config.open_street_map)
        case VectorTileServerNameEnum.OPEN_FREE_MAP:
            assert config.open_free_map is not None, "config.open_free_map should be not none"
            return OpenFreeMapVectorTileServer(config.open_free_map)
        case VectorTileServerNameEnum.VERSATILES:
            assert config.versatiles is not None, "config.versatiles should be not none"
            return VersatilesVectorTileServer(config.versatiles)

from abc import ABC

from django.core.exceptions import ValidationError

from utils.common import validate_imagery_url

from .config import VectorConfig, VectorTileServerNameEnum
from .models import (
    VectorTileServerCommonConfig,
    VectorTileServerConfig,
    VectorTileServerCustomConfig,
)


class BaseVectorTileServerException(Exception): ...


class _BaseVectorTileServer(ABC):
    """Create a tile server class."""

    type: VectorTileServerNameEnum
    url: str
    source_name: str
    credits: str | None

    # FIXME(tnagorra): We might need to move this to pydantic object
    @staticmethod
    def check_imagery_url(url: str) -> bool:
        try:
            validate_imagery_url(url, support_quadkey=False)
            return True
        except ValidationError as e:
            raise BaseVectorTileServerException(e.message) from e


class CustomVectorTileServer(_BaseVectorTileServer):
    type = VectorTileServerNameEnum.CUSTOM

    def __init__(
        self,
        config: VectorTileServerCustomConfig,
    ):
        self.url = config.url
        self.source_name = config.source_name
        self.credits = config.credits


class OpenStreetMapVectorTileServer(_BaseVectorTileServer):
    type = VectorTileServerNameEnum.OPEN_STREET_MAP
    url = VectorConfig.VECTOR_IMAGE_URLS[VectorTileServerNameEnum.OPEN_STREET_MAP]

    def __init__(
        self,
        config: VectorTileServerCommonConfig,
    ):
        self.source_name = config.source_name
        self.credits = config.credits


class OpenFreeMapVectorTileServer(_BaseVectorTileServer):
    type = VectorTileServerNameEnum.OPEN_FREE_MAP
    url = VectorConfig.VECTOR_IMAGE_URLS[VectorTileServerNameEnum.OPEN_FREE_MAP]

    def __init__(
        self,
        config: VectorTileServerCommonConfig,
    ):
        self.source_name = config.source_name
        self.credits = config.credits


class VersatilesVectorTileServer(_BaseVectorTileServer):
    type = VectorTileServerNameEnum.VERSATILES
    url = VectorConfig.VECTOR_IMAGE_URLS[VectorTileServerNameEnum.VERSATILES]

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

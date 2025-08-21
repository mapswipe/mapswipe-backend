import strawberry

from apps.common.models import IconEnum
from utils.custom_options.models import CustomOption, CustomSubOption
from utils.geo.raster_tile_server.config import RasterTileServerNameEnum
from utils.geo.raster_tile_server.models import (
    RasterTileServerCommonConfig,
    RasterTileServerConfig,
    RasterTileServerCustomConfig,
)
from utils.geo.vector_tile_server.config import VectorTileServerNameEnum
from utils.geo.vector_tile_server.models import (
    VectorTileServerCommonConfig,
    VectorTileServerConfig,
    VectorTileServerCustomConfig,
)


# Custom options
@strawberry.experimental.pydantic.type(model=CustomSubOption, all_fields=True)
class ProjectCustomSubOption: ...


@strawberry.experimental.pydantic.type(model=CustomOption, all_fields=True)
class ProjectCustomOption: ...


# Static tile servers
@strawberry.type
class VectorTileServerType:
    type: VectorTileServerNameEnum
    label: str
    url: str
    layers: list[str]
    min_zoom: int | None
    max_zoom: int | None
    credits: str


@strawberry.type
class RasterTileServerType:
    type: RasterTileServerNameEnum
    label: str
    url: str
    # FIXME(tnagorra): We can implement min_zoom and max_zoom
    # after we update rendering of tiles in the app from images to maplibre
    min_zoom: int | None
    max_zoom: int | None
    credits: str


@strawberry.type
class RasterTileServersType:
    vector: list[VectorTileServerType]
    raster: list[RasterTileServerType]


@strawberry.type
class CustomOptionType:
    title: str
    icon: IconEnum
    value: int
    description: str
    icon_color: str


# Tile server
@strawberry.experimental.pydantic.type(model=RasterTileServerCustomConfig, all_fields=True)
class ProjectRasterTileServerCustomConfig: ...


@strawberry.experimental.pydantic.type(model=RasterTileServerCommonConfig, all_fields=True)
class ProjectRasterTileServerCommonConfig: ...


@strawberry.experimental.pydantic.type(model=RasterTileServerConfig, all_fields=True)
class ProjectRasterTileServerConfig: ...


# Vector tile server
@strawberry.experimental.pydantic.type(model=VectorTileServerCustomConfig, all_fields=True)
class ProjectVectorTileServerCustomConfig: ...


@strawberry.experimental.pydantic.type(model=VectorTileServerCommonConfig, all_fields=True)
class ProjectVectorTileServerCommonConfig: ...


@strawberry.experimental.pydantic.type(model=VectorTileServerConfig, all_fields=True)
class ProjectVectorTileServerConfig: ...

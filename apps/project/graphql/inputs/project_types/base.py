import strawberry

from utils.geo.raster_tile_server.models import (
    RasterTileServerCommonConfig,
    RasterTileServerConfig,
    RasterTileServerCustomConfig,
)
from utils.geo.vector_tile_server.models import (
    VectorTileServerCommonConfig,
    VectorTileServerConfig,
    VectorTileServerCustomConfig,
)


# Tile server
@strawberry.experimental.pydantic.input(model=RasterTileServerCustomConfig, all_fields=True)
class RasterTileServerCustomConfigInput: ...


@strawberry.experimental.pydantic.input(model=RasterTileServerCommonConfig, all_fields=True)
class RasterTileServerCommonConfigInput: ...


# FIXME(tnagorra): Add one_of here?
@strawberry.experimental.pydantic.input(model=RasterTileServerConfig, all_fields=True)
class ProjectRasterTileServerConfigInput: ...


# Vector tile server
@strawberry.experimental.pydantic.input(model=VectorTileServerCustomConfig, all_fields=True)
class VectorTileServerCustomConfigInput: ...


@strawberry.experimental.pydantic.input(model=VectorTileServerCommonConfig, all_fields=True)
class VectorTileServerCommonConfigInput: ...


# FIXME(tnagorra): Add one_of here?
@strawberry.experimental.pydantic.input(model=VectorTileServerConfig, all_fields=True)
class ProjectVectorTileServerConfigInput: ...

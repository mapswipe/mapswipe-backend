import strawberry

from utils.geo.tile_server.models import (
    TileServerCommonConfig,
    TileServerConfig,
    TileServerCustomConfig,
)
from utils.geo.vector_tile_server.models import (
    VectorTileServerCommonConfig,
    VectorTileServerConfig,
    VectorTileServerCustomConfig,
)


# Tile server
@strawberry.experimental.pydantic.input(model=TileServerCustomConfig, all_fields=True)
class TileServerCustomConfigInput: ...


@strawberry.experimental.pydantic.input(model=TileServerCommonConfig, all_fields=True)
class TileServerCommonConfigInput: ...


# FIXME(tnagorra): Add one_of here?
@strawberry.experimental.pydantic.input(model=TileServerConfig, all_fields=True)
class ProjectTileServerConfigInput: ...


# Vector tile server
@strawberry.experimental.pydantic.input(model=VectorTileServerCustomConfig, all_fields=True)
class VectorTileServerCustomConfigInput: ...


@strawberry.experimental.pydantic.input(model=VectorTileServerCommonConfig, all_fields=True)
class VectorTileServerCommonConfigInput: ...


# FIXME(tnagorra): Add one_of here?
@strawberry.experimental.pydantic.input(model=VectorTileServerConfig, all_fields=True)
class ProjectVectorTileServerConfigInput: ...

import typing

from pydantic import BaseModel

from utils.geo.tile_server.tile_server import TileServerName


class CustomTileServerConfig(BaseModel):
    name: typing.Literal[TileServerName.CUSTOM]
    url: str
    credits: str | None = None


class CommonTileServerConfig(BaseModel):
    name: TileServerName
    credits: str | None = None


TileServerConfigAlias: typing.TypeAlias = CustomTileServerConfig | CommonTileServerConfig

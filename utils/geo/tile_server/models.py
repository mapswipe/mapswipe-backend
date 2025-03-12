import typing

from pydantic import BaseModel

from utils.geo.tile_server.tile_server import TileServerNameEnum


class CustomTileServerConfig(BaseModel):
    name: typing.Literal[TileServerNameEnum.CUSTOM]
    url: str
    credits: str | None = None


class CommonTileServerConfig(BaseModel):
    name: TileServerNameEnum
    credits: str | None = None


TileServerConfigAlias: typing.TypeAlias = CustomTileServerConfig | CommonTileServerConfig

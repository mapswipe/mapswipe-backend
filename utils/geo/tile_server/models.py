import typing

from pydantic import BaseModel, Field, field_validator, model_validator

from .config import TileServerNameEnum, VectorTileServerNameEnum


class TileServerCustomConfig(BaseModel):
    # NOTE: URL validation is currently defined in BaseTileServer.check_imagery_url
    url: typing.Annotated[str, Field(strict=True, max_length=1000)]
    credits: typing.Annotated[str | None, Field(strict=True, max_length=1000)] = None


class TileServerCommonConfig(BaseModel):
    credits: typing.Annotated[str | None, Field(strict=True, max_length=1000)] = None


class TileServerConfig(BaseModel):
    name: TileServerNameEnum

    custom: TileServerCustomConfig | None = None
    bing: TileServerCommonConfig | None = None
    mapbox: TileServerCommonConfig | None = None
    maxar_standard: TileServerCommonConfig | None = None
    maxar_premium: TileServerCommonConfig | None = None
    esri: TileServerCommonConfig | None = None
    esri_beta: TileServerCommonConfig | None = None

    @field_validator("name", mode="before")
    def ensure_name_enum(cls, value: str | TileServerNameEnum | None):
        if isinstance(value, str):
            return TileServerNameEnum(value)
        return value

    @model_validator(mode="after")
    def check_valid_data(self) -> typing.Self:
        match self.name:
            case TileServerNameEnum.CUSTOM:
                if self.custom is None:
                    raise ValueError("custom config is required")
                return self
            case TileServerNameEnum.BING:
                if self.bing is None:
                    raise ValueError("bing config is required")
                return self
            case TileServerNameEnum.MAPBOX:
                if self.mapbox is None:
                    raise ValueError("mapbox config is required")
                return self
            case TileServerNameEnum.MAXAR_PREMIUM:
                if self.maxar_premium is None:
                    raise ValueError("maxar premium config is required")
                return self
            case TileServerNameEnum.MAXAR_STANDARD:
                if self.maxar_standard is None:
                    raise ValueError("maxar standard config is required")
                return self
            case TileServerNameEnum.ESRI:
                if self.esri is None:
                    raise ValueError("ESRI config is required")
                return self
            case TileServerNameEnum.ESRI_BETA:
                if self.esri_beta is None:
                    raise ValueError("ESRI (Beta) config is required")
                return self

    @model_validator(mode="after")
    def check_tile_server_config(self) -> typing.Self:
        from .tile_server import BaseTileServerException, get_tile_server

        try:
            get_tile_server(self)
        except BaseTileServerException as e:
            raise ValueError(e) from None
        return self


class VectorTileServerCustomConfig(BaseModel):
    # FIXME(tnagorra): need to add URL validation
    url: typing.Annotated[str, Field(strict=True, max_length=1000)]
    source_name: typing.Annotated[str | None, Field(strict=True, max_length=1000)] = None
    credits: typing.Annotated[str | None, Field(strict=True, max_length=1000)] = None


class VectorTileServerCommonConfig(BaseModel):
    source_name: typing.Annotated[str | None, Field(strict=True, max_length=1000)] = None
    credits: typing.Annotated[str | None, Field(strict=True, max_length=1000)] = None


class VectorTileServerConfig(BaseModel):
    name: VectorTileServerNameEnum

    custom: VectorTileServerCustomConfig | None = None
    open_street_map: VectorTileServerCommonConfig | None = None
    open_free_map: VectorTileServerCommonConfig | None = None
    versatiles: VectorTileServerCommonConfig | None = None

    @field_validator("name", mode="before")
    def ensure_name_enum(cls, value: str | TileServerNameEnum | None):
        if isinstance(value, str):
            return VectorTileServerNameEnum(value)
        return value

    @model_validator(mode="after")
    def check_valid_data(self) -> typing.Self:
        match self.name:
            case VectorTileServerNameEnum.CUSTOM:
                if self.custom is None:
                    raise ValueError("custom config is required")
                return self
            case VectorTileServerNameEnum.OPEN_STREET_MAP:
                if self.open_street_map is None:
                    raise ValueError("open street map config is required")
                return self
            case VectorTileServerNameEnum.OPEN_FREE_MAP:
                if self.open_free_map is None:
                    raise ValueError("open free map config is required")
                return self
            case VectorTileServerNameEnum.VERSATILES:
                if self.versatiles is None:
                    raise ValueError("versatiles config is required")
                return self

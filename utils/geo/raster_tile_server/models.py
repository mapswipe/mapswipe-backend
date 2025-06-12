import typing

from pydantic import BaseModel, Field, field_validator, model_validator

from .config import RasterTileServerNameEnum


class RasterTileServerCustomConfig(BaseModel):
    # NOTE: URL validation is currently defined in BaseRasterTileServer.check_imagery_url
    url: typing.Annotated[str, Field(strict=True, max_length=1000)]
    credits: typing.Annotated[str, Field(strict=True, max_length=1000)]


class RasterTileServerCommonConfig(BaseModel):
    credits: typing.Annotated[str, Field(strict=True, max_length=1000)]


class RasterTileServerConfig(BaseModel):
    name: RasterTileServerNameEnum

    custom: RasterTileServerCustomConfig | None = None
    bing: RasterTileServerCommonConfig | None = None
    mapbox: RasterTileServerCommonConfig | None = None
    maxar_standard: RasterTileServerCommonConfig | None = None
    maxar_premium: RasterTileServerCommonConfig | None = None
    esri: RasterTileServerCommonConfig | None = None
    esri_beta: RasterTileServerCommonConfig | None = None

    @field_validator("name", mode="before")
    def ensure_name_enum(cls, value: str | RasterTileServerNameEnum | None):
        if isinstance(value, str):
            return RasterTileServerNameEnum(value)
        return value

    @model_validator(mode="after")
    def check_valid_data(self) -> typing.Self:
        match self.name:
            case RasterTileServerNameEnum.CUSTOM:
                if self.custom is None:
                    raise ValueError("custom config is required")
                return self
            case RasterTileServerNameEnum.BING:
                if self.bing is None:
                    raise ValueError("bing config is required")
                return self
            case RasterTileServerNameEnum.MAPBOX:
                if self.mapbox is None:
                    raise ValueError("mapbox config is required")
                return self
            case RasterTileServerNameEnum.MAXAR_PREMIUM:
                if self.maxar_premium is None:
                    raise ValueError("maxar premium config is required")
                return self
            case RasterTileServerNameEnum.MAXAR_STANDARD:
                if self.maxar_standard is None:
                    raise ValueError("maxar standard config is required")
                return self
            case RasterTileServerNameEnum.ESRI:
                if self.esri is None:
                    raise ValueError("ESRI config is required")
                return self
            case RasterTileServerNameEnum.ESRI_BETA:
                if self.esri_beta is None:
                    raise ValueError("ESRI (Beta) config is required")
                return self

    @model_validator(mode="after")
    def check_raster_tile_server_config(self) -> typing.Self:
        from .raster_tile_server import BaseVectorTileServerException, get_raster_tile_server

        try:
            get_raster_tile_server(self)
        except BaseVectorTileServerException as e:
            raise ValueError(e) from None
        return self

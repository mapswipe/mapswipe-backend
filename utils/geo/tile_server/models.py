import typing

from pydantic import BaseModel, model_validator

from .config import TileServerNameEnum


class TileServerCustomConfig(BaseModel):
    # NOTE: Validation is currently defined in BaseTileServer.check_imagery_url
    # TODO(tnagorra): Max length should be 1000
    url: str

    # TODO(tnagorra): Max length should be 1000
    credits: str | None = None


class TileServerCommonConfig(BaseModel):
    # TODO(tnagorra): Max length should be 1000
    credits: str | None = None


class TileServerConfig(BaseModel):
    name: TileServerNameEnum

    custom: TileServerCustomConfig | None = None
    bing: TileServerCommonConfig | None = None
    mapbox: TileServerCommonConfig | None = None
    maxar_standard: TileServerCommonConfig | None = None
    maxar_premium: TileServerCommonConfig | None = None
    esri: TileServerCommonConfig | None = None
    esri_beta: TileServerCommonConfig | None = None

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

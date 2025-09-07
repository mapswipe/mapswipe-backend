import typing

from pydantic import BaseModel, field_validator, model_validator

from utils import fields as custom_fields
from utils.geo.tile_functions import tile_coords_and_zoom_to_quad_key

from .config import RasterConfig, RasterTileServerNameEnum, RasterTileServerNormConfig


class RasterTileServerCustomConfig(BaseModel):
    url: custom_fields.PydanticRasterTileServerUrl
    credits: custom_fields.PydanticLongText
    min_zoom: int | None = None
    max_zoom: int | None = None


class RasterTileServerCommonConfig(BaseModel):
    credits: custom_fields.PydanticLongText


class RasterTileServerConfig(BaseModel):
    name: RasterTileServerNameEnum

    custom: RasterTileServerCustomConfig | None = None
    bing: RasterTileServerCommonConfig | None = None
    mapbox: RasterTileServerCommonConfig | None = None
    maxar_standard: RasterTileServerCommonConfig | None = None
    maxar_premium: RasterTileServerCommonConfig | None = None
    esri: RasterTileServerCommonConfig | None = None
    esri_beta: RasterTileServerCommonConfig | None = None

    def get_config(self) -> RasterTileServerNormConfig:
        if self.name == RasterTileServerNameEnum.CUSTOM:
            assert self.custom is not None
            return {
                "url": self.custom.url,
                "raw_url": self.custom.url,
                "api_key": "",
                "credits": self.custom.credits,
                "min_zoom": self.custom.min_zoom,
                "max_zoom": self.custom.max_zoom,
            }
        return RasterConfig.get_config(self.name)

    def generate_url(self, tile_x: int, tile_y: int, tile_z: int) -> str:
        url = self.get_config()["url"]
        if "{quad_key}" in url:
            quad_key = tile_coords_and_zoom_to_quad_key(tile_x, tile_y, tile_z)
            return url.format(
                quad_key=quad_key,
            )
        return url.format(
            x=tile_x,
            y=tile_y,
            z=tile_z,
        )

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

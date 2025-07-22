import typing

from pydantic import BaseModel, field_validator, model_validator

from utils import fields as custom_fields

from .config import VectorConfig, VectorTileServerNameEnum, VectorTileServerNormConfig


class VectorTileServerCustomConfig(BaseModel):
    url: custom_fields.PydanticVectorTileServerUrl
    source_name: custom_fields.PydanticLongText
    credits: custom_fields.PydanticLongText
    min_zoom: custom_fields.PydanticZoomLevel
    max_zoom: custom_fields.PydanticZoomLevel


class VectorTileServerCommonConfig(BaseModel):
    source_name: custom_fields.PydanticLongText
    credits: custom_fields.PydanticLongText


class VectorTileServerConfig(BaseModel):
    name: VectorTileServerNameEnum

    custom: VectorTileServerCustomConfig | None = None
    open_street_map: VectorTileServerCommonConfig | None = None
    open_free_map: VectorTileServerCommonConfig | None = None
    versatiles: VectorTileServerCommonConfig | None = None

    def get_config(self) -> VectorTileServerNormConfig:
        if self.name == VectorTileServerNameEnum.CUSTOM:
            assert self.custom is not None
            return {
                "url": self.custom.url,
                "credits": self.custom.credits,
                "min_zoom": self.custom.min_zoom,
                "max_zoom": self.custom.max_zoom,
                "layers": [self.custom.source_name],
            }
        return VectorConfig.get_config(self.name)

    # FIXME(tnagorra): Do we need this?
    @field_validator("name", mode="before")
    def ensure_name_enum(cls, value: str | VectorTileServerNameEnum | None):
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

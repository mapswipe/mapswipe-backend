import typing

from pydantic import BaseModel, Field, field_validator, model_validator

from .config import VectorTileServerNameEnum


class VectorTileServerCustomConfig(BaseModel):
    # FIXME(tnagorra): need to add URL validation
    url: typing.Annotated[str, Field(strict=True, max_length=1000)]
    source_name: typing.Annotated[str, Field(strict=True, max_length=1000)]
    credits: typing.Annotated[str, Field(strict=True, max_length=1000)]
    min_zoom: typing.Annotated[int, Field(strict=True, ge=0, lt=23)]
    max_zoom: typing.Annotated[int, Field(strict=True, ge=0, lt=23)]


class VectorTileServerCommonConfig(BaseModel):
    source_name: typing.Annotated[str, Field(strict=True, max_length=1000)]
    credits: typing.Annotated[str, Field(strict=True, max_length=1000)]


class VectorTileServerConfig(BaseModel):
    name: VectorTileServerNameEnum

    custom: VectorTileServerCustomConfig | None = None
    open_street_map: VectorTileServerCommonConfig | None = None
    open_free_map: VectorTileServerCommonConfig | None = None
    versatiles: VectorTileServerCommonConfig | None = None

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

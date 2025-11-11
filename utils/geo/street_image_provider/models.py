from typing import assert_never

from django.db import models
from pydantic import BaseModel, field_validator

from utils import fields as custom_fields


class StreetImageProviderNameEnum(models.TextChoices):
    MAPILLARY = "mapillary", "Mapillary"
    PANORAMAX = "panoramax", "Panoramax (Metacatalog API)"
    PANORAMAX_CUSTOM = "panoramax_custom", "Panoramax (Custom API URL)"


class StreetImageProvider(BaseModel):
    name: StreetImageProviderNameEnum
    url: custom_fields.PydanticUrl | None = None

    @field_validator("url", mode="after")
    @classmethod
    def url_only_for_custom_panoramax(cls, v, info):
        if v is not None and info.data.get("name") != StreetImageProviderNameEnum.PANORAMAX_CUSTOM:
            raise ValueError("url field is only allowed for PANORAMAX_CUSTOM provider")
        if v is None and info.data.get("name") == StreetImageProviderNameEnum.PANORAMAX_CUSTOM:
            raise ValueError("url field is required for PANORAMAX_CUSTOM provider")
        return v

    @property
    def tile_level(self) -> int:
        if self.name == StreetImageProviderNameEnum.MAPILLARY:
            return 14
        if self.name == StreetImageProviderNameEnum.PANORAMAX or self.name == StreetImageProviderNameEnum.PANORAMAX_CUSTOM:
            return 15
        assert_never(self.name)

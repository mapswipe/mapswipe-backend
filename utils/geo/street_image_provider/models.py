from typing import Self, assert_never
from urllib.parse import urlsplit

from django.db import models
from pydantic import BaseModel, field_validator, model_validator

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
    def url_as_domain(cls, url: str | None) -> str | None:
        # NOTE: The API paths are appended to the url, so only the domain is accepted
        if url is None:
            return url
        parts = urlsplit(url)
        if parts.path not in ("", "/") or parts.query or parts.fragment:
            raise ValueError("url must be the domain of the Panoramax instance, without a path")
        return f"{parts.scheme}://{parts.netloc}/"

    @model_validator(mode="after")
    def url_only_for_custom_panoramax(self) -> Self:
        if self.name == StreetImageProviderNameEnum.PANORAMAX_CUSTOM:
            if self.url is None:
                raise ValueError("url field is required for PANORAMAX_CUSTOM provider")
        elif self.url is not None:
            raise ValueError("url field is only allowed for PANORAMAX_CUSTOM provider")
        return self

    @property
    def tile_level(self) -> int:
        if self.name == StreetImageProviderNameEnum.MAPILLARY:
            return 14
        if self.name == StreetImageProviderNameEnum.PANORAMAX or self.name == StreetImageProviderNameEnum.PANORAMAX_CUSTOM:
            return 15
        assert_never(self.name)

import re
import typing

from django.db import models
from pydantic import BaseModel, field_validator, model_validator
from pyfirebase_mapswipe import models as firebase_models

from main.config import Config
from utils import fields as custom_fields

# NOTE: IPv6 and non-ASCII hosts are rejected, so IDNs must be entered in punycode
_URL_RE = re.compile(r"https?://(?P<authority>[^/?#]*)(?P<rest>.*)", re.DOTALL)
_HOST_PORT_RE = re.compile(
    r"(?:"
    r"(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
    r"|(?![\d.]+(?::|$))[a-z\d](?:[a-z\d-]{0,61}[a-z\d])?(?:\.[a-z\d](?:[a-z\d-]{0,61}[a-z\d])?)*"
    r")(?::(?P<port>[1-9]\d{0,4}))?",
    re.IGNORECASE,
)


class StreetImageProviderEnum(models.TextChoices):
    MAPILLARY = "mapillary", "Mapillary"
    PANORAMAX = "panoramax", "Panoramax (public catalog)"
    PANORAMAX_CUSTOM = "panoramax_custom", "Panoramax (custom instance)"


class StreetImageFilters(BaseModel):
    pano_only: custom_fields.PydanticBool | None = None
    creator_id: custom_fields.PydanticLongText | None = None
    start_time: custom_fields.PydanticDate | None = None
    end_time: custom_fields.PydanticDate | None = None
    randomize_order: custom_fields.PydanticBool = False
    sampling_threshold: custom_fields.PydanticStrictNonNegativeInt | None = None


class StreetMapillaryConfig(StreetImageFilters):
    organization_id: custom_fields.PydanticLongText | None = None


class StreetPanoramaxConfig(StreetImageFilters): ...


class StreetPanoramaxCustomConfig(StreetImageFilters):
    url: custom_fields.PydanticLongText

    @field_validator("url", mode="after")
    @classmethod
    def validate_url_is_domain(cls, url: str) -> str:
        if url != url.strip():
            raise ValueError("url must not have leading or trailing whitespace")
        # NOTE: The API paths are appended to the url as entered, so only the scheme and host are accepted
        url_match = _URL_RE.fullmatch(url)
        if url_match is None:
            raise ValueError("url must start with http:// or https://")
        if url_match["rest"] not in ("", "/"):
            raise ValueError("url must not have a path, query or fragment")
        if "@" in url_match["authority"]:
            raise ValueError("url must not have credentials")
        host_port_match = _HOST_PORT_RE.fullmatch(url_match["authority"])
        if host_port_match is None or (host_port_match["port"] and int(host_port_match["port"]) > 65535):
            raise ValueError("url must have a valid hostname or IPv4 address and an optional port")
        return url


class StreetImageProviderNormConfig(typing.TypedDict):
    name: StreetImageProviderEnum
    url: str
    tile_level: int


class StreetImageNormFilters(typing.TypedDict):
    pano_only: bool | None
    creator_id: str | None
    organization_id: str | None
    start_time: str | None
    end_time: str | None
    randomize_order: bool
    sampling_threshold: int | None


class StreetImageProviderConfig(BaseModel):
    provider: StreetImageProviderEnum

    mapillary: StreetMapillaryConfig | None = None
    panoramax: StreetPanoramaxConfig | None = None
    panoramax_custom: StreetPanoramaxCustomConfig | None = None

    def _get_provider_configs(self) -> dict[StreetImageProviderEnum, StreetImageFilters | None]:
        return {
            StreetImageProviderEnum.MAPILLARY: self.mapillary,
            StreetImageProviderEnum.PANORAMAX: self.panoramax,
            StreetImageProviderEnum.PANORAMAX_CUSTOM: self.panoramax_custom,
        }

    @model_validator(mode="after")
    def check_valid_data(self) -> typing.Self:
        for provider, config in self._get_provider_configs().items():
            if provider == self.provider and config is None:
                raise ValueError(f"{provider.value} config is required")
            if provider != self.provider and config is not None:
                raise ValueError(f"{provider.value} config is only allowed for the {provider.value} provider")
        return self

    def get_config(self) -> StreetImageProviderNormConfig:
        match self.provider:
            case StreetImageProviderEnum.MAPILLARY:
                return {"name": self.provider, "url": Config.MAPILLARY_API_LINK, "tile_level": 14}
            case StreetImageProviderEnum.PANORAMAX:
                return {"name": self.provider, "url": Config.PANORAMAX_API_LINK, "tile_level": 15}
            case StreetImageProviderEnum.PANORAMAX_CUSTOM:
                assert self.panoramax_custom is not None
                return {"name": self.provider, "url": self.panoramax_custom.url, "tile_level": 15}
            case _:
                typing.assert_never(self.provider)

    def get_filters(self) -> StreetImageNormFilters:
        filters = self._get_provider_configs()[self.provider]
        assert filters is not None
        return {
            "pano_only": filters.pano_only,
            "creator_id": filters.creator_id,
            # NOTE: Panoramax features have no organization_id, so filtering by it would match nothing
            "organization_id": self.mapillary.organization_id if self.mapillary is not None else None,
            "start_time": filters.start_time,
            "end_time": filters.end_time,
            "randomize_order": filters.randomize_order,
            "sampling_threshold": filters.sampling_threshold,
        }

    def get_firebase_image_provider(self) -> firebase_models.FbObjImageProvider:
        return firebase_models.FbObjImageProvider(
            name=self.provider.value,
            url=self.panoramax_custom.url if self.panoramax_custom is not None else None,
        )

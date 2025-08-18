import typing
from urllib.parse import unquote

from django.core.exceptions import ValidationError
from django.utils.translation import gettext
from pydantic import BeforeValidator, Field, HttpUrl, TypeAdapter

from utils.common import validate_imagery_url

http_url_adapter = TypeAdapter(HttpUrl)


# FIXME(tnagorra): Separate out django and pydantic fields


def _validate_url(value: typing.Any):
    url = str(http_url_adapter.validate_python(value))
    # NOTE: url is encoded by validate_python so placeholders like {x} {y} {z} are encoded
    # we need to decode them
    return unquote(url)


def _validate_raster_tile_url(value: typing.Any):
    url = _validate_url(value)
    validate_imagery_url(value, support_quad_key=True)
    return url


def _validate_vector_tile_url(value: typing.Any):
    url = _validate_url(value)
    validate_imagery_url(value, support_quad_key=False)
    return url


# Ref: https://github.com/pydantic/pydantic/discussions/6395#discussioncomment-7361416
PydanticUrl = typing.Annotated[str, BeforeValidator(_validate_url)]

PydanticRasterTileServerUrl = typing.Annotated[str, BeforeValidator(_validate_raster_tile_url)]

PydanticVectorTileServerUrl = typing.Annotated[str, BeforeValidator(_validate_vector_tile_url)]

PydanticLongText = typing.Annotated[str, Field(strict=True, max_length=1000)]

PydanticLat = typing.Annotated[float, Field(strict=True, ge=-90, le=90)]
PydanticLng = typing.Annotated[float, Field(strict=True, ge=-180, le=180)]

PydanticOpacity = typing.Annotated[
    float,
    Field(
        ge=0.0,
        le=1.0,
        description="A valid opacity like 0.2 or 1.0",
    ),
]

PydanticPositiveFloat = typing.Annotated[
    float,
    Field(
        ge=0.0,
        description="A positive float value",
    ),
]
PydanticPositiveInt = typing.Annotated[
    int,
    Field(
        ge=0,
        description="A positive int value",
    ),
]

PydanticHexColor = typing.Annotated[
    str,
    Field(
        pattern=r"^#(?:[0-9a-fA-F]{3}){1,2}$",
        description="A valid hex color string like '#fff' or '#ffffff'",
    ),
]

PydanticId = typing.Annotated[str, Field(strict=True, pattern=r"^\d+$")]

PydanticRestrictedZoomLevel = typing.Annotated[int, Field(strict=True, gt=13, lt=23)]

PydanticZoomLevel = typing.Annotated[int, Field(strict=True, ge=0, lt=23)]

# FIXME(frozenhelium): add proper validation
PydanticUlid = typing.Annotated[str, Field(strict=True, pattern=r"^[0-9A-Z]{26}$")]


PydanticIsPano = typing.Annotated[
    bool | None,
    Field(
        default=False,
        description="Filter for images that are panoramas.",
    ),
]

PydanticCreatorId = typing.Annotated[
    str | None,
    Field(
        default=None,
        description="Filter for images created by a specific user.",
    ),
]

PydanticOrganizationId = typing.Annotated[
    str | None,
    Field(
        default=None,
        description="Filter for images that belong to a specific organization.",
    ),
]

PydanticStartTime = typing.Annotated[
    str | None,
    Field(
        default=None,
        description="Filter for images captured after this timestamp.",
    ),
]

PydanticEndTime = typing.Annotated[
    str | None,
    Field(
        default=None,
        description="Filter for images captured before this timestamp.",
    ),
]

PydanticRandomizeOrder = typing.Annotated[
    bool,
    Field(
        default=False,
        description="Randomize the order of the images.",
    ),
]

PydanticSamplingThreshold = typing.Annotated[
    int | None,
    Field(
        default=None,
        description="Sampling threshold for filtering images.",
    ),
]


def validate_percentage(value: float | int):
    if not (0 <= value <= 100):
        raise ValidationError(
            gettext("The value %(value)s is not a valid percentage. It should be between 0 and 100."),
            params={"value": value},
        )

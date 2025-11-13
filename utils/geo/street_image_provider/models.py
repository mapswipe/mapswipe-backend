from enum import Enum

from pydantic import BaseModel

from utils import fields as custom_fields


class StreetImageProviderNameEnum(str, Enum):
    MAPILLARY = "mapillary"
    PANORAMAX = "panoramax"


class StreetImageProvider(BaseModel):
    name: StreetImageProviderNameEnum | None = None
    url: custom_fields.PydanticUrl | None = None

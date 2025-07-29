from pydantic import BaseModel

from apps.common.models import IconEnum
from utils import fields as custom_fields


class CustomSubOption(BaseModel):
    client_id: custom_fields.PydanticUlid
    value: custom_fields.PydanticPositiveInt
    description: custom_fields.PydanticLongText


class CustomOption(BaseModel):
    client_id: custom_fields.PydanticUlid
    value: custom_fields.PydanticPositiveInt
    title: custom_fields.PydanticLongText
    description: custom_fields.PydanticLongText
    icon: IconEnum
    icon_color: custom_fields.PydanticHexColor

    sub_options: list[CustomSubOption] | None

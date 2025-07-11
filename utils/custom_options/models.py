import enum

from pydantic import BaseModel

from utils import fields as custom_fields


class CustomOptionIconEnum(enum.Enum):
    ADD_OUTLINE = "add-outline"
    ALERT_OUTLINE = "alert-outline"
    BAN_OUTLINE = "ban-outline"
    CHECK = "check"
    CLOSE_OUTLINE = "close-outline"
    CHECKMARK_OUTLINE = "checkmark-outline"
    EGG_OUTLINE = "egg-outline"
    ELLIPSE_OUTLINE = "ellipse-outline"
    FLAG_OUTLINE = "flag-outline"
    HAND_LEFT_OUTLINE = "hand-left-outline"
    HAND_RIGHT_OUTLINE = "hand-right-outline"
    HAPPY_OUTLINE = "happy-outline"
    HEART_OUTLINE = "heart-outline"
    HELP_OUTLINE = "help-outline"
    INFORMATION_OUTLINE = "information-outline"
    PRISM_OUTLINE = "prism-outline"
    REFRESH_OUTLINE = "refresh-outline"
    REMOVE_OUTLINE = "remove-outline"
    SAD_OUTLINE = "sad-outline"
    SEARCH_OUTLINE = "search-outline"
    SHAPES_OUTLINE = "shapes-outline"
    SQUARE_OUTLINE = "square-outline"
    STAR_OUTLINE = "star-outline"
    THUMBS_DOWN_OUTLINE = "thumbs-down-outline"
    THUMBS_UP_OUTLINE = "thumbs-up-outline"
    TRIANGLE_OUTLINE = "triangle-outline"
    WARNING_OUTLINE = "warning-outline"
    GENERAL_TAP = "general-tap"
    TAP = "tap"
    TAP_1 = "tap-1"
    TAP_2 = "tap-2"
    TAP_3 = "tap-3"
    SWIPE_LEFT = "swipe-left"


class CustomSubOption(BaseModel):
    value: custom_fields.PydanticPositiveInt
    description: custom_fields.PydanticLongText


class CustomOption(BaseModel):
    value: custom_fields.PydanticPositiveInt
    title: custom_fields.PydanticLongText
    description: custom_fields.PydanticLongText
    icon: CustomOptionIconEnum
    icon_color: custom_fields.PydanticHexColor

    sub_options: list[CustomSubOption] | None

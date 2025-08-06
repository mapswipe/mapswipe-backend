from typing import TypedDict

from apps.common.models import IconEnum

from .models import ProjectTypeEnum


class CustomOption(TypedDict):
    title: str
    icon: IconEnum
    value: int
    description: str
    icon_color: str


class CustomOptionDefaults:
    VALIDATE: list[CustomOption] = [
        {
            "title": "Yes",
            "icon": IconEnum.CHECKMARK_OUTLINE,
            "value": 1,
            "description": "the shape does outline a building in the image",
            "icon_color": "#388E3C",
        },
        {
            "title": "No",
            "icon": IconEnum.CLOSE_OUTLINE,
            "value": 0,
            "description": "the shape doesn't match a building in the image",
            "icon_color": "#D32F2F",
        },
        {
            "title": "Not Sure",
            "icon": IconEnum.REMOVE_OUTLINE,
            "value": 2,
            "description": "if you're not sure or unsure about the image",
            "icon_color": "#616161",
        },
    ]

    VALIDATE_IMAGE: list[CustomOption] = [
        {
            "title": "Yes",
            "icon": IconEnum.CHECKMARK_OUTLINE,
            "value": 1,
            "description": "the image contains the feature",
            "icon_color": "#388E3C",
        },
        {
            "title": "No",
            "icon": IconEnum.CLOSE_OUTLINE,
            "value": 0,
            "description": "the image does not contain the feature",
            "icon_color": "#D32F2F",
        },
        {
            "title": "Not Sure",
            "icon": IconEnum.REMOVE_OUTLINE,
            "value": 2,
            "description": "it's not clear if the image contains the feature",
            "icon_color": "#616161",
        },
    ]


def get_custom_options(project_type: ProjectTypeEnum):
    if project_type == ProjectTypeEnum.VALIDATE:
        return CustomOptionDefaults.VALIDATE
    if project_type == ProjectTypeEnum.VALIDATE_IMAGE:
        return CustomOptionDefaults.VALIDATE_IMAGE
    return []

import typing
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
            "description": "you're not sure or there is cloud cover/bad imagery",
            "icon_color": "#616161",
        },
        {
            "title": "Offset",
            "icon": IconEnum.FLAG_OUTLINE,
            "value": 3,
            "description": "building outline is correct, but not aligned to the imagery",
            "icon_color": "#ff9800",
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

    STREET: list[CustomOption] = [
        {
            "title": "Yes",
            "icon": IconEnum.CHECKMARK_OUTLINE,
            "value": 1,
            "description": "the object you are looking for is in the image",
            "icon_color": "#388E3C",
        },
        {
            "title": "No",
            "icon": IconEnum.CLOSE_OUTLINE,
            "value": 0,
            "description": "the object you are looking for is NOT in the image",
            "icon_color": "#D32F2F",
        },
        {
            "title": "Not Sure",
            "icon": IconEnum.REMOVE_OUTLINE,
            "value": 2,
            "description": "if you're not sure or there is bad imagery",
            "icon_color": "#616161",
        },
    ]

    LOCATE: list[CustomOption] = [
        {
            "title": "Single Feature",
            "icon": IconEnum.CHECKMARK_OUTLINE,
            "value": 1,
            "description": "the shape outlines a single feature in the image",
            "icon_color": "#388E3C",
        },
        {
            "title": "No",
            "icon": IconEnum.CLOSE_OUTLINE,
            "value": 0,
            "description": "the shape does not outline any feature in the image",
            "icon_color": "#D32F2F",
        },
        {
            "title": "Multiple Features",
            "icon": IconEnum.CHECKMARK_OUTLINE,
            "value": 2,
            "description": "the shape outlines multiple features in the image",
            "icon_color": "#ffff00",
        },
    ]


def get_custom_options(project_type: ProjectTypeEnum) -> list[CustomOption]:
    if project_type == ProjectTypeEnum.VALIDATE:
        return CustomOptionDefaults.VALIDATE
    if project_type == ProjectTypeEnum.VALIDATE_IMAGE:
        return CustomOptionDefaults.VALIDATE_IMAGE
    if project_type == ProjectTypeEnum.STREET:
        return CustomOptionDefaults.STREET
    if project_type == ProjectTypeEnum.LOCATE:
        return CustomOptionDefaults.LOCATE
    return []


def get_fallback_custom_options_for_export(project_type: ProjectTypeEnum) -> list[int]:
    # FIXME: Should we throw error for validate, validate image and street instead?
    if project_type == ProjectTypeEnum.VALIDATE:
        return [item["value"] for item in CustomOptionDefaults.VALIDATE]
    if project_type == ProjectTypeEnum.VALIDATE_IMAGE:
        return [item["value"] for item in CustomOptionDefaults.VALIDATE_IMAGE]
    if project_type == ProjectTypeEnum.STREET:
        return [item["value"] for item in CustomOptionDefaults.STREET]
    if project_type == ProjectTypeEnum.LOCATE:
        return [item["value"] for item in CustomOptionDefaults.LOCATE]

    if (
        project_type == ProjectTypeEnum.FIND
        or project_type == ProjectTypeEnum.COMPARE
        or project_type == ProjectTypeEnum.COMPLETENESS
    ):
        return [
            0,  # No
            1,  # Yes
            2,  # Maybe
            3,  # Bad Imagery
        ]
    typing.assert_never(project_type)

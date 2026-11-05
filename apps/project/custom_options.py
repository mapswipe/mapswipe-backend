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
            "icon_color": "transparent",
        },
        {
            "title": "Multiple Features",
            "icon": IconEnum.CHECKMARK_OUTLINE,
            "value": 2,
            "description": "the shape outlines multiple features in the image",
            "icon_color": "#ffff00",
        },
    ]

    # NOTE: Unlike the options above, which are user-definable per project, the
    # FIND, COMPARE and COMPLETENESS project types have no `custom_options`.
    # Users cannot define their own; these fixed defaults are the only options these
    # project types can use.
    FIND_COMPARE_COMPLETENESS: list[CustomOption] = [
        {
            "title": "Yes",
            "icon": IconEnum.CHECKMARK_OUTLINE,
            "value": 1,
            "description": "",
            "icon_color": "#388E3C",
        },
        {
            "title": "No",
            "icon": IconEnum.CLOSE_OUTLINE,
            "value": 0,
            "description": "",
            "icon_color": "#D32F2F",
        },
        {
            "title": "Maybe",
            "icon": IconEnum.REMOVE_OUTLINE,
            "value": 2,
            "description": "",
            "icon_color": "#616161",
        },
        {
            "title": "Bad Imagery",
            "icon": IconEnum.ALERT_OUTLINE,
            "value": 3,
            "description": "",
            "icon_color": "#ff9800",
        },
    ]


def get_custom_options(project_type: ProjectTypeEnum) -> list[CustomOption]:
    # User-definable: these defaults are only a starting point and can be overridden
    # per project
    if project_type == ProjectTypeEnum.VALIDATE:
        return CustomOptionDefaults.VALIDATE
    if project_type == ProjectTypeEnum.VALIDATE_IMAGE:
        return CustomOptionDefaults.VALIDATE_IMAGE
    if project_type == ProjectTypeEnum.STREET:
        return CustomOptionDefaults.STREET
    if project_type == ProjectTypeEnum.LOCATE:
        return CustomOptionDefaults.LOCATE
    # Fixed: these cannot be defined by the user,
    # so these are the only options they can use.
    if (
        project_type == ProjectTypeEnum.FIND
        or project_type == ProjectTypeEnum.COMPARE
        or project_type == ProjectTypeEnum.COMPLETENESS
    ):
        return CustomOptionDefaults.FIND_COMPARE_COMPLETENESS
    typing.assert_never(project_type)

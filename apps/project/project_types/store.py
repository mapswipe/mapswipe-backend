import typing

from apps.project.models import ProjectTypeEnum

from .tile_map_service.change_detection.project import ChangeDetectionProject
from .tile_map_service.classification.project import ClassificationProject

ProjectTypeHandlers: typing.TypeAlias = typing.Type[ChangeDetectionProject | ClassificationProject]


@typing.overload
def get_project_type_handler(
    project_type: typing.Literal[ProjectTypeEnum.BUILD_AREA],
) -> typing.Type[ClassificationProject]: ...


@typing.overload
def get_project_type_handler(
    project_type: typing.Literal[ProjectTypeEnum.CHANGE_DETECTION],
) -> typing.Type[ChangeDetectionProject]: ...


@typing.overload
def get_project_type_handler(
    project_type: typing.Literal[ProjectTypeEnum.COMPLETENESS],
) -> typing.Type[ChangeDetectionProject]: ...


def get_project_type_handler(project_type: ProjectTypeEnum) -> ProjectTypeHandlers:
    match project_type:
        case ProjectTypeEnum.BUILD_AREA:
            return ClassificationProject
        case ProjectTypeEnum.CHANGE_DETECTION:
            return ChangeDetectionProject
        case ProjectTypeEnum.COMPLETENESS:
            return ClassificationProject

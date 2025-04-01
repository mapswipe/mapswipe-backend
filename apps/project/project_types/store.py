import typing

from apps.project.models import ProjectTypeEnum

from .tile_map_service.change_detection.project import ChangeDetectionProject
from .tile_map_service.classification.project import ClassificationProject

type ProjectTypeHandlers = type[ChangeDetectionProject | ClassificationProject]


@typing.overload
def get_project_type_handler(
    project_type: typing.Literal[ProjectTypeEnum.BUILD_AREA],
) -> type[ClassificationProject]: ...


@typing.overload
def get_project_type_handler(
    project_type: typing.Literal[ProjectTypeEnum.CHANGE_DETECTION],
) -> type[ChangeDetectionProject]: ...


@typing.overload
def get_project_type_handler(
    project_type: typing.Literal[ProjectTypeEnum.COMPLETENESS],
) -> type[ChangeDetectionProject]: ...


def get_project_type_handler(project_type: ProjectTypeEnum) -> ProjectTypeHandlers:
    match project_type:
        case ProjectTypeEnum.BUILD_AREA:
            return ClassificationProject
        case ProjectTypeEnum.CHANGE_DETECTION:
            return ChangeDetectionProject
        case ProjectTypeEnum.COMPLETENESS:
            return ClassificationProject

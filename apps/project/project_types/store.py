import typing

from apps.project.models import ProjectTypeEnum

from .tile_map_service.change_detection.project import ChangeDetectionProject
from .tile_map_service.find.project import FindProject

type ProjectTypeHandlers = type[ChangeDetectionProject | FindProject]


@typing.overload
def get_project_type_handler(
    project_type: typing.Literal[ProjectTypeEnum.FIND],
) -> type[FindProject]: ...


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
        case ProjectTypeEnum.FIND:
            return FindProject
        case ProjectTypeEnum.CHANGE_DETECTION:
            return ChangeDetectionProject
        case ProjectTypeEnum.COMPLETENESS:
            return FindProject

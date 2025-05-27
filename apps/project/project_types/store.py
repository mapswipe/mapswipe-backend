import typing

from apps.project.models import ProjectTypeEnum

from .tile_map_service.compare.project import CompareProject
from .tile_map_service.completeness.project import CompletenessProject
from .tile_map_service.find.project import FindProject
from .validate.project import ValidateProject

type ProjectTypeHandlers = type[CompareProject | ValidateProject | FindProject | CompletenessProject]


@typing.overload
def get_project_type_handler(
    project_type: typing.Literal[ProjectTypeEnum.FIND],
) -> type[FindProject]: ...


@typing.overload
def get_project_type_handler(
    project_type: typing.Literal[ProjectTypeEnum.COMPARE],
) -> type[CompareProject]: ...


@typing.overload
def get_project_type_handler(
    project_type: typing.Literal[ProjectTypeEnum.VALIDATE],
) -> type[ValidateProject]: ...


@typing.overload
def get_project_type_handler(
    project_type: typing.Literal[ProjectTypeEnum.COMPLETENESS],
) -> type[CompletenessProject]: ...


def get_project_type_handler(project_type: ProjectTypeEnum) -> ProjectTypeHandlers:
    match project_type:
        case ProjectTypeEnum.FIND:
            return FindProject
        case ProjectTypeEnum.COMPARE:
            return CompareProject
        case ProjectTypeEnum.VALIDATE:
            return ValidateProject
        case ProjectTypeEnum.COMPLETENESS:
            return CompletenessProject

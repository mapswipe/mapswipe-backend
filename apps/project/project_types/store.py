import typing

from apps.project.models import ProjectTypeEnum

from .tile_map_service.compare.project import CompareProject, CompareProjectProperty
from .tile_map_service.completeness.project import CompletenessProject, CompletenessProjectProperty
from .tile_map_service.find.project import FindProject, FindProjectProperty
from .validate.project import ValidateProject, ValidateProjectProperty


def get_project_property(project_type: ProjectTypeEnum | None):
    if project_type is None:
        return None
    if project_type == ProjectTypeEnum.COMPARE:
        return ("compare", CompareProjectProperty)
    if project_type == ProjectTypeEnum.FIND:
        return ("find", FindProjectProperty)
    if project_type == ProjectTypeEnum.VALIDATE:
        return ("validate", ValidateProjectProperty)
    if project_type == ProjectTypeEnum.COMPLETENESS:
        return ("completeness", CompletenessProjectProperty)
    typing.assert_never(project_type)


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

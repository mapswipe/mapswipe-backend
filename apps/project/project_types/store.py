import typing

from apps.project.models import ProjectTypeEnum

from .tile_map_service.change_detection.project import ChangeDetectionProject
from .tile_map_service.classification.project import ClassificationProject

ProjecTypeHandlers: typing.TypeAlias = ChangeDetectionProject | ClassificationProject


@typing.overload
def get_project_type_handler(project_type: typing.Literal[ProjectTypeEnum.BUILD_AREA]) -> ClassificationProject: ...


@typing.overload
def get_project_type_handler(project_type: typing.Literal[ProjectTypeEnum.CHANGE_DETECTION]) -> ChangeDetectionProject: ...


@typing.overload
def get_project_type_handler(project_type: typing.Literal[ProjectTypeEnum.COMPLETENESS]) -> ChangeDetectionProject: ...


def get_project_type_handler(project_type: ProjectTypeEnum) -> ProjecTypeHandlers:
    return {
        ProjectTypeEnum.BUILD_AREA: ClassificationProject,
        ProjectTypeEnum.CHANGE_DETECTION: ChangeDetectionProject,
        ProjectTypeEnum.COMPLETENESS: ClassificationProject,
    }[project_type]

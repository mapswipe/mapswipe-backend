import typing

from apps.project.models import ProjectType

from .tile_map_service.change_detection.project import ChangeDetectionProject
from .tile_map_service.classification.project import ClassificationProject

ProjecTypeHandlers: typing.TypeAlias = ChangeDetectionProject | ClassificationProject


@typing.overload
def get_project_type_handler(project_type: typing.Literal[ProjectType.BUILD_AREA]) -> ClassificationProject: ...


@typing.overload
def get_project_type_handler(project_type: typing.Literal[ProjectType.CHANGE_DETECTION]) -> ChangeDetectionProject: ...


@typing.overload
def get_project_type_handler(project_type: typing.Literal[ProjectType.COMPLETENESS]) -> ChangeDetectionProject: ...


def get_project_type_handler(project_type: ProjectType) -> ProjecTypeHandlers:
    return {
        ProjectType.BUILD_AREA: ClassificationProject,
        ProjectType.CHANGE_DETECTION: ChangeDetectionProject,
        ProjectType.COMPLETENESS: ClassificationProject,
    }[project_type]

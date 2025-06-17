import typing

from apps.project.models import ProjectTypeEnum

from .tile_map_service.compare import tutorial as compare_tutorial
from .tile_map_service.compare.project import CompareProject, CompareProjectProperty
from .tile_map_service.completeness import tutorial as completeness_tutorial
from .tile_map_service.completeness.project import CompletenessProject, CompletenessProjectProperty
from .tile_map_service.find import tutorial as find_tutorial
from .tile_map_service.find.project import FindProject, FindProjectProperty
from .validate import tutorial as validate_tutorial
from .validate.project import ValidateProject, ValidateProjectProperty
from .validate_image import tutorial as validate_image_tutorial
from .validate_image.project import ValidateImageProject, ValidateImageProjectProperty


# FIXME(tnagorra): Move this to store
def get_tutorial_task_property(project_type: ProjectTypeEnum | None):
    if project_type is None:
        return None
    if project_type == ProjectTypeEnum.COMPARE:
        return ("compare", compare_tutorial.CompareTutorialTaskProperty)
    if project_type == ProjectTypeEnum.FIND:
        return ("find", find_tutorial.FindTutorialTaskProperty)
    if project_type == ProjectTypeEnum.VALIDATE:
        return ("validate", validate_tutorial.ValidateTutorialTaskProperty)
    if project_type == ProjectTypeEnum.VALIDATE_IMAGE:
        # TODO(tnagorra): Need to confirm if validate_image or validateImage
        return ("validate_image", validate_image_tutorial.ValidateImageTutorialTaskProperty)
    if project_type == ProjectTypeEnum.COMPLETENESS:
        return ("completeness", completeness_tutorial.CompletenessTutorialTaskProperty)
    typing.assert_never(project_type)


def get_project_property(project_type: ProjectTypeEnum | None):
    if project_type is None:
        return None
    if project_type == ProjectTypeEnum.COMPARE:
        return ("compare", CompareProjectProperty)
    if project_type == ProjectTypeEnum.FIND:
        return ("find", FindProjectProperty)
    if project_type == ProjectTypeEnum.VALIDATE:
        return ("validate", ValidateProjectProperty)
    if project_type == ProjectTypeEnum.VALIDATE_IMAGE:
        # TODO(tnagorra): Need to confirm if validate_image or validateImage
        return ("validate_image", ValidateImageProjectProperty)
    if project_type == ProjectTypeEnum.COMPLETENESS:
        return ("completeness", CompletenessProjectProperty)
    typing.assert_never(project_type)


type ProjectTypeHandlers = type[CompareProject | ValidateProject | ValidateImageProject | FindProject | CompletenessProject]


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
    project_type: typing.Literal[ProjectTypeEnum.VALIDATE_IMAGE],
) -> type[ValidateImageProject]: ...


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
        case ProjectTypeEnum.VALIDATE_IMAGE:
            return ValidateImageProject

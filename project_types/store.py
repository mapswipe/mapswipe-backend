import typing

from apps.project.models import ProjectTypeEnum
from project_types.street.project import StreetProject, StreetProjectProperty
from project_types.street.tutorial import StreetTutorial, StreetTutorialTaskProperty

from .tile_map_service.compare.project import CompareProject, CompareProjectProperty
from .tile_map_service.compare.tutorial import CompareTutorial, CompareTutorialTaskProperty
from .tile_map_service.completeness.project import CompletenessProject, CompletenessProjectProperty
from .tile_map_service.completeness.tutorial import CompletenessTutorial, CompletenessTutorialTaskProperty
from .tile_map_service.find.project import FindProject, FindProjectProperty
from .tile_map_service.find.tutorial import FindTutorial, FindTutorialTaskProperty
from .tile_map_service.locate.project import LocateProject, LocateProjectProperty
from .tile_map_service.locate.tutorial import LocateTutorial, LocateTutorialTaskProperty
from .validate.project import ValidateProject, ValidateProjectProperty
from .validate.tutorial import ValidateTutorial, ValidateTutorialTaskProperty
from .validate_image.project import ValidateImageProject, ValidateImageProjectProperty
from .validate_image.tutorial import ValidateImageTutorial, ValidateImageTutorialTaskProperty


def get_tutorial_task_property(project_type: ProjectTypeEnum | None):
    if project_type is None:
        return None
    if project_type == ProjectTypeEnum.COMPARE:
        return ("compare", CompareTutorialTaskProperty)
    if project_type == ProjectTypeEnum.FIND:
        return ("find", FindTutorialTaskProperty)
    if project_type == ProjectTypeEnum.VALIDATE:
        return ("validate", ValidateTutorialTaskProperty)
    if project_type == ProjectTypeEnum.VALIDATE_IMAGE:
        # TODO(tnagorra): Need to confirm if validate_image or validateImage
        return ("validate_image", ValidateImageTutorialTaskProperty)
    if project_type == ProjectTypeEnum.COMPLETENESS:
        return ("completeness", CompletenessTutorialTaskProperty)
    if project_type == ProjectTypeEnum.STREET:
        return ("street", StreetTutorialTaskProperty)
    if project_type == ProjectTypeEnum.LOCATE:
        return ("locate", LocateTutorialTaskProperty)
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
    if project_type == ProjectTypeEnum.STREET:
        return ("street", StreetProjectProperty)
    if project_type == ProjectTypeEnum.LOCATE:
        return ("locate", LocateProjectProperty)
    typing.assert_never(project_type)


type ProjectTypeHandlers = type[
    CompareProject
    | ValidateProject
    | ValidateImageProject
    | FindProject
    | CompletenessProject
    | StreetProject
    | LocateProject
]


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


@typing.overload
def get_project_type_handler(
    project_type: typing.Literal[ProjectTypeEnum.STREET],
) -> type[StreetProject]: ...


@typing.overload
def get_project_type_handler(
    project_type: typing.Literal[ProjectTypeEnum.LOCATE],
) -> type[LocateProject]: ...


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
        case ProjectTypeEnum.STREET:
            return StreetProject
        case ProjectTypeEnum.LOCATE:
            return LocateProject


type TutorialTypeHandlers = type[
    CompareTutorial
    | ValidateTutorial
    | FindTutorial
    | CompletenessTutorial
    | ValidateImageTutorial
    | StreetTutorial
    | LocateTutorial
]


@typing.overload
def get_tutorial_type_handler(
    tutorial_type: typing.Literal[ProjectTypeEnum.FIND],
) -> type[FindTutorial]: ...


@typing.overload
def get_tutorial_type_handler(
    tutorial_type: typing.Literal[ProjectTypeEnum.COMPARE],
) -> type[CompareTutorial]: ...


@typing.overload
def get_tutorial_type_handler(
    tutorial_type: typing.Literal[ProjectTypeEnum.VALIDATE],
) -> type[ValidateTutorial]: ...


@typing.overload
def get_tutorial_type_handler(
    tutorial_type: typing.Literal[ProjectTypeEnum.COMPLETENESS],
) -> type[CompletenessTutorial]: ...


@typing.overload
def get_tutorial_type_handler(
    tutorial_type: typing.Literal[ProjectTypeEnum.VALIDATE_IMAGE],
) -> type[ValidateImageTutorial]: ...


@typing.overload
def get_tutorial_type_handler(
    tutorial_type: typing.Literal[ProjectTypeEnum.STREET],
) -> type[typing.Any]: ...


@typing.overload
def get_tutorial_type_handler(
    tutorial_type: typing.Literal[ProjectTypeEnum.LOCATE],
) -> type[typing.Any]: ...


def get_tutorial_type_handler(tutorial_type: ProjectTypeEnum) -> TutorialTypeHandlers:
    match tutorial_type:
        case ProjectTypeEnum.FIND:
            return FindTutorial
        case ProjectTypeEnum.COMPARE:
            return CompareTutorial
        case ProjectTypeEnum.VALIDATE:
            return ValidateTutorial
        case ProjectTypeEnum.COMPLETENESS:
            return CompletenessTutorial
        case ProjectTypeEnum.VALIDATE_IMAGE:
            return ValidateImageTutorial
        case ProjectTypeEnum.STREET:
            return StreetTutorial
        case ProjectTypeEnum.LOCATE:
            return LocateTutorial

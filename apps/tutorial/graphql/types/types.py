import typing

import strawberry
import strawberry_django
from django.db import models

from apps.common.graphql.types import CommonAssetTypeMixin, UserResourceTypeMixin
from apps.project.models import Project, ProjectTypeEnum
from apps.tutorial.models import (
    Tutorial,
    TutorialAsset,
    TutorialInformationPage,
    TutorialInformationPageBlock,
    TutorialScenarioPage,
    TutorialTask,
)
from project_types.tile_map_service.compare import tutorial as compare_tutorial
from project_types.tile_map_service.completeness import tutorial as completeness_tutorial
from project_types.tile_map_service.find import tutorial as find_tutorial
from project_types.validate import tutorial as validate_tutorial
from project_types.validate_image import tutorial as validate_image_tutorial

from .project_types.compare import CompareTutorialTaskPropertyType
from .project_types.completeness import CompletenessTutorialTaskPropertyType
from .project_types.find import FindTutorialTaskPropertyType
from .project_types.validate import ValidateTutorialTaskPropertyType
from .project_types.validate_image import ValidateImageTutorialTaskPropertyType


@strawberry_django.type(TutorialTask)
class TutorialTaskType(UserResourceTypeMixin):
    id: strawberry.ID
    scenario_id: strawberry.ID
    reference: strawberry.auto

    @strawberry_django.field(
        only=["project_type_specifics"],
        annotate={
            "project_type": models.F("scenario__tutorial__project__project_type"),
        },
    )
    async def project_type_specifics(
        self,
        task: strawberry.Parent[TutorialTask],
    ) -> (
        CompareTutorialTaskPropertyType
        | FindTutorialTaskPropertyType
        | ValidateTutorialTaskPropertyType
        | ValidateImageTutorialTaskPropertyType
        | CompletenessTutorialTaskPropertyType
        | None
    ):
        data = task.project_type_specifics
        project_type_enum = ProjectTypeEnum(task.project_type)  # type: ignore[reportAttributeAccessIssue]

        if data is None:
            return None
        if project_type_enum == Project.Type.FIND:
            return typing.cast("FindTutorialTaskPropertyType", find_tutorial.FindTutorialTaskProperty.model_validate(data))
        if project_type_enum == Project.Type.VALIDATE:
            return typing.cast(
                "ValidateTutorialTaskPropertyType",
                validate_tutorial.ValidateTutorialTaskProperty.model_validate(data),
            )
        if project_type_enum == Project.Type.VALIDATE_IMAGE:
            return typing.cast(
                "ValidateImageTutorialTaskPropertyType",
                validate_image_tutorial.ValidateImageTutorialTaskProperty.model_validate(data),
            )
        if project_type_enum == Project.Type.COMPARE:
            return typing.cast(
                "CompareTutorialTaskPropertyType",
                compare_tutorial.CompareTutorialTaskProperty.model_validate(data),
            )
        if project_type_enum == Project.Type.COMPLETENESS:
            return typing.cast(
                "CompletenessTutorialTaskPropertyType",
                completeness_tutorial.CompletenessTutorialTaskProperty.model_validate(data),
            )
        typing.assert_never(project_type_enum)


@strawberry_django.type(TutorialScenarioPage)
class TutorialScenarioPageType(UserResourceTypeMixin):
    id: strawberry.ID
    tutorial_id: strawberry.ID
    scenario_page_number: strawberry.auto
    instructions_description: strawberry.auto
    instructions_icon: strawberry.auto
    instructions_title: strawberry.auto
    hint_description: strawberry.auto
    hint_icon: strawberry.auto
    hint_title: strawberry.auto
    success_description: strawberry.auto
    success_icon: strawberry.auto
    success_title: strawberry.auto
    tasks: list[TutorialTaskType]


@strawberry_django.type(TutorialInformationPageBlock)
class TutorialInformationPageBlockType(UserResourceTypeMixin):
    id: strawberry.ID
    page_id: strawberry.ID
    block_number: strawberry.auto
    block_type: strawberry.auto
    text: strawberry.auto
    image: strawberry.auto


@strawberry_django.type(TutorialInformationPage)
class TutorialInformationPageType(UserResourceTypeMixin):
    id: strawberry.ID
    tutorial_id: strawberry.ID
    title: strawberry.auto
    page_number: strawberry.auto
    blocks: list[TutorialInformationPageBlockType]


@strawberry_django.type(Tutorial)
class TutorialType(UserResourceTypeMixin):
    id: strawberry.ID
    name: strawberry.auto
    project_id: strawberry.ID
    status: strawberry.auto

    # FIXME(tnagorra): The ordering is not always being applied on queries
    # The tests are failing randomly.
    scenarios: list[TutorialScenarioPageType]
    information_pages: list[TutorialInformationPageType]


@strawberry_django.type(TutorialAsset)
class TutorialAssetType(UserResourceTypeMixin, CommonAssetTypeMixin):
    id: strawberry.ID
    file: strawberry.auto
    tutorial_id: strawberry.ID

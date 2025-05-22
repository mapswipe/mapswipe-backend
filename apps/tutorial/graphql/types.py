import typing

import strawberry
import strawberry_django
from django.db import models

from apps.common.graphql.types import UserResourceTypeMixin
from apps.project.models import Project, ProjectTypeEnum
from apps.tutorial.models import (
    Tutorial,
    TutorialInformationPage,
    TutorialInformationPageBlock,
    TutorialScenarioPage,
    TutorialTask,
)
from apps.tutorial.project_types.tile_map_service.compare import tutorial as compare_tutorial
from apps.tutorial.project_types.tile_map_service.completeness import tutorial as completeness_tutorial
from apps.tutorial.project_types.tile_map_service.find import tutorial as find_tutorial


# Project Properties
@strawberry.experimental.pydantic.type(model=compare_tutorial.CompareTutorialTaskProperty, all_fields=True)
class CompareTutorialTaskPropertyType: ...


@strawberry.experimental.pydantic.type(model=find_tutorial.FindTutorialTaskProperty, all_fields=True)
class FindTutorialTaskPropertyType: ...


@strawberry.experimental.pydantic.type(model=completeness_tutorial.CompletenessTutorialTaskProperty, all_fields=True)
class CompletenessTutorialTaskPropertyType: ...


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
    ) -> CompareTutorialTaskPropertyType | FindTutorialTaskPropertyType | CompletenessTutorialTaskPropertyType | None:
        data = task.project_type_specifics
        project_type_enum = ProjectTypeEnum(task.project_type)  # type: ignore[reportAttributeAccessIssue]

        if data is None:
            return None
        if project_type_enum == Project.Type.FIND:
            return typing.cast("FindTutorialTaskPropertyType", find_tutorial.FindTutorialTaskProperty.model_validate(data))
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
    project_id: strawberry.ID
    status: strawberry.auto

    scenarios: list[TutorialScenarioPageType]
    information_pages: list[TutorialInformationPageType]

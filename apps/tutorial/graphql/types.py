import strawberry
import strawberry_django

from apps.common.graphql.types import UserResourceTypeMixin
from apps.tutorial.models import (
    Tutorial,
    TutorialInformationPage,
    TutorialInformationPageBlock,
    TutorialScenarioPage,
    TutorialTask,
)


@strawberry_django.type(TutorialTask)
class TutorialTaskType:
    id: strawberry.ID
    scenario_id: strawberry.ID
    reference: strawberry.auto
    # FIXME(tnagorra): Make this typesafe
    project_type_specifics: strawberry.auto


@strawberry_django.type(TutorialScenarioPage)
class TutorialScenarioPageType:
    id: strawberry.ID
    tutorial_id: strawberry.ID
    scenario_id: strawberry.auto
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
class TutorialInformationPageBlockType:
    id: strawberry.ID
    page_id: strawberry.ID
    block_number: strawberry.auto
    block_type: strawberry.auto
    text: strawberry.auto
    # TODO(tnagorra) Add image


@strawberry_django.type(TutorialInformationPage)
class TutorialInformationPageType:
    id: strawberry.ID
    tutorial_id: strawberry.ID
    title: strawberry.auto
    page_number: strawberry.auto
    blocks: list[TutorialInformationPageBlockType]


@strawberry_django.type(Tutorial)
class TutorialType(UserResourceTypeMixin):
    id: strawberry.ID
    project_id: strawberry.ID
    is_draft: strawberry.auto

    scenarios: list[TutorialScenarioPageType]
    information_pages: list[TutorialInformationPageType]

import strawberry
import strawberry_django
from strawberry.file_uploads import Upload

from apps.tutorial.models import (
    Tutorial,
    TutorialInformationPage,
    TutorialInformationPageBlock,
    TutorialScenarioPage,
    TutorialTask,
)


@strawberry.input
class DeleteInput:
    id: strawberry.ID


@strawberry.interface
class CudInput:
    delete: DeleteInput | None = strawberry.UNSET


@strawberry_django.input(TutorialTask)
class TutorialTaskCreateInput:
    # NOTE: scenario_id will be referenced from parent

    reference: strawberry.auto
    # FIXME(tnagorra): Make this typesafe
    project_type_specifics: strawberry.auto


@strawberry_django.partial(TutorialTask)
class TutorialTaskUpdateInput:
    # NOTE: scenario_id will be referenced from parent

    id: strawberry.ID
    reference: strawberry.auto
    # FIXME(tnagorra): Make this typesafe
    project_type_specifics: strawberry.auto


@strawberry.input
class TutorialTaskInput(CudInput):
    create: TutorialTaskCreateInput | None = strawberry.UNSET
    update: TutorialTaskUpdateInput | None = strawberry.UNSET


@strawberry_django.input(TutorialScenarioPage)
class TutorialScenarioPageCreateInput:
    # NOTE: tutorial_id will be referenced from parent

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
    tasks: list[TutorialTaskCreateInput]


@strawberry_django.partial(TutorialScenarioPage)
class TutorialScenarioPageUpdateInput:
    # NOTE: tutorial_id will be referenced from parent

    id: strawberry.ID
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
    tasks: list[TutorialTaskInput] | None = strawberry.UNSET


@strawberry_django.input(TutorialTask)
class TutorialScenarioPageInput(CudInput):
    create: TutorialScenarioPageCreateInput | None = strawberry.UNSET
    update: TutorialScenarioPageUpdateInput | None = strawberry.UNSET


@strawberry_django.input(TutorialInformationPageBlock)
class TutorialInformationPageBlockCreateInput:
    # NOTE: page_id will be referenced from parent

    block_number: strawberry.auto
    block_type: strawberry.auto
    text: strawberry.auto
    image: Upload | None = strawberry.UNSET


@strawberry_django.partial(TutorialInformationPageBlock)
class TutorialInformationPageBlockUpdateInput:
    # NOTE: page_id will be referenced from parent

    id: strawberry.ID
    block_number: strawberry.auto
    block_type: strawberry.auto
    text: strawberry.auto
    image: Upload | None = strawberry.UNSET


@strawberry.input
class TutorialInformationPageBlockInput(CudInput):
    create: TutorialInformationPageBlockCreateInput | None = strawberry.UNSET
    update: TutorialInformationPageBlockUpdateInput | None = strawberry.UNSET


@strawberry_django.input(TutorialInformationPage)
class TutorialInformationPageCreateInput:
    # NOTE: tutorial_id will be referenced from parent

    title: strawberry.auto
    page_number: strawberry.auto
    blocks: list[TutorialInformationPageBlockCreateInput]


@strawberry_django.partial(TutorialInformationPage)
class TutorialInformationPageUpdateInput:
    # NOTE: tutorial_id will be referenced from parent

    id: strawberry.ID
    title: strawberry.auto
    page_number: strawberry.auto
    blocks: list[TutorialInformationPageBlockInput] | None = strawberry.UNSET


@strawberry.input
class TutorialInformationPageInput(CudInput):
    create: TutorialInformationPageCreateInput | None = strawberry.UNSET
    update: TutorialInformationPageUpdateInput | None = strawberry.UNSET


# NOTE: Make sure this matches with the serializers ../serializers.py
@strawberry_django.input(Tutorial)
class TutorialCreateInput:
    project: strawberry.ID
    is_draft: strawberry.auto

    scenarios: list[TutorialScenarioPageCreateInput]
    information_pages: list[TutorialInformationPageCreateInput]


# NOTE: Make sure this matches with the serializers ../serializers.py
@strawberry_django.partial(Tutorial)
class TutorialUpdateInput:
    id: strawberry.ID
    project: strawberry.ID
    is_draft: strawberry.auto

    scenarios: list[TutorialScenarioPageInput] | None = strawberry.UNSET
    information_pages: list[TutorialInformationPageInput] | None = strawberry.UNSET

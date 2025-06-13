import strawberry
import strawberry_django
from strawberry.file_uploads import Upload

from apps.common.graphql.inputs import (
    UserResourceCreateInputMixin,
    UserResourceTopLevelUpdateInputMixin,
    UserResourceUpdateInputMixin,
)
from apps.tutorial.models import (
    Tutorial,
    TutorialInformationPage,
    TutorialInformationPageBlock,
    TutorialScenarioPage,
    TutorialTask,
)
from utils.graphql.types import CudInput

from .project_types.compare import CompareTutorialTaskPropertyInput
from .project_types.completeness import CompletenessTutorialTaskPropertyInput
from .project_types.find import FindTutorialTaskPropertyInput
from .project_types.validate import ValidateTutorialTaskPropertyInput


@strawberry.input(one_of=True)
class TutorialTaskProjectTypeSpecificInput:
    compare: CompareTutorialTaskPropertyInput | None = strawberry.UNSET
    find: FindTutorialTaskPropertyInput | None = strawberry.UNSET
    validate: ValidateTutorialTaskPropertyInput | None = strawberry.UNSET
    completeness: CompletenessTutorialTaskPropertyInput | None = strawberry.UNSET


@strawberry_django.input(TutorialTask)
class TutorialTaskCreateInput(UserResourceCreateInputMixin):
    # NOTE: scenario_id will be referenced from parent

    reference: strawberry.auto
    project_type_specifics: TutorialTaskProjectTypeSpecificInput


@strawberry_django.partial(TutorialTask)
class TutorialTaskUpdateInput(UserResourceUpdateInputMixin):
    # NOTE: scenario_id will be referenced from parent

    reference: strawberry.auto
    project_type_specifics: TutorialTaskProjectTypeSpecificInput


@strawberry.input
class TutorialTaskInput(CudInput[TutorialTaskCreateInput, TutorialTaskUpdateInput]): ...


@strawberry_django.input(TutorialScenarioPage)
class TutorialScenarioPageCreateInput(UserResourceCreateInputMixin):
    # NOTE: tutorial_id will be referenced from parent

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
    tasks: list[TutorialTaskCreateInput]


@strawberry_django.partial(TutorialScenarioPage)
class TutorialScenarioPageUpdateInput(UserResourceUpdateInputMixin):
    # NOTE: tutorial_id will be referenced from parent

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
    tasks: list[TutorialTaskInput] | None = strawberry.UNSET


@strawberry_django.input(TutorialTask)
class TutorialScenarioPageInput(CudInput[TutorialScenarioPageCreateInput, TutorialScenarioPageUpdateInput]): ...


@strawberry_django.input(TutorialInformationPageBlock)
class TutorialInformationPageBlockCreateInput(UserResourceCreateInputMixin):
    # NOTE: page_id will be referenced from parent

    block_number: strawberry.auto
    block_type: strawberry.auto
    text: strawberry.auto
    image: Upload | None = strawberry.UNSET


@strawberry_django.partial(TutorialInformationPageBlock)
class TutorialInformationPageBlockUpdateInput(UserResourceUpdateInputMixin):
    # NOTE: page_id will be referenced from parent

    block_number: strawberry.auto
    block_type: strawberry.auto
    text: strawberry.auto
    image: Upload | None = strawberry.UNSET


@strawberry.input
class TutorialInformationPageBlockInput(
    CudInput[TutorialInformationPageBlockCreateInput, TutorialInformationPageBlockUpdateInput],
): ...


@strawberry_django.input(TutorialInformationPage)
class TutorialInformationPageCreateInput(UserResourceCreateInputMixin):
    # NOTE: tutorial_id will be referenced from parent

    title: strawberry.auto
    page_number: strawberry.auto
    blocks: list[TutorialInformationPageBlockCreateInput]


@strawberry_django.partial(TutorialInformationPage)
class TutorialInformationPageUpdateInput(UserResourceUpdateInputMixin):
    # NOTE: tutorial_id will be referenced from parent

    title: strawberry.auto
    page_number: strawberry.auto
    blocks: list[TutorialInformationPageBlockInput] | None = strawberry.UNSET


@strawberry.input
class TutorialInformationPageInput(CudInput[TutorialInformationPageCreateInput, TutorialInformationPageUpdateInput]): ...


# NOTE: Make sure this matches with the serializers ../serializers.py
@strawberry_django.input(Tutorial)
class TutorialCreateInput(UserResourceCreateInputMixin):
    project: strawberry.ID
    name: strawberry.auto

    scenarios: list[TutorialScenarioPageCreateInput]
    information_pages: list[TutorialInformationPageCreateInput]


# NOTE: Make sure this matches with the serializers ../serializers.py
@strawberry_django.partial(Tutorial)
class TutorialUpdateInput(UserResourceTopLevelUpdateInputMixin):
    project: strawberry.ID
    name: strawberry.auto
    status: strawberry.auto

    scenarios: list[TutorialScenarioPageInput] | None = strawberry.UNSET
    information_pages: list[TutorialInformationPageInput] | None = strawberry.UNSET

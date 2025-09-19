import factory
from factory.django import DjangoModelFactory
from ulid import ULID

from apps.common.models import IconEnum

from .models import (
    Tutorial,
    TutorialInformationPage,
    TutorialInformationPageBlock,
    TutorialScenarioPage,
    TutorialTask,
)


class TutorialFactory(DjangoModelFactory):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Tutorial

    firebase_id = factory.LazyFunction(lambda: str(ULID()))
    client_id = factory.LazyFunction(lambda: str(ULID()))
    # name = factory.Sequence(lambda n: f"Tutorial {n}")


class TutorialScenarioPageFactory(DjangoModelFactory):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = TutorialScenarioPage

    client_id = factory.LazyFunction(lambda: str(ULID()))
    scenario_page_number = factory.Sequence(lambda n: n)
    instructions_icon = IconEnum.ADD_OUTLINE
    instructions_title = factory.Sequence(lambda n: f"Instruction title for page {n}")

    hint_description = factory.Sequence(lambda n: f"Hint description for page {n}")
    hint_icon = IconEnum.ADD_OUTLINE
    hint_title = factory.Sequence(lambda n: f"Hint title for page {n}")

    success_description = factory.Sequence(lambda n: f"success description for page {n}")
    success_icon = IconEnum.ADD_OUTLINE
    success_title = factory.Sequence(lambda n: f"success title for page {n}")


class TutorialTaskFactory(DjangoModelFactory):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = TutorialTask

    client_id = factory.LazyFunction(lambda: str(ULID()))
    reference = 1
    project_type_specifics = factory.LazyAttribute(lambda _: {})


class TutorialInformationPageFactory(DjangoModelFactory):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = TutorialInformationPage

    client_id = factory.LazyFunction(lambda: str(ULID()))
    title = factory.Sequence(lambda n: f"Page {n}")
    page_number = factory.Sequence(lambda n: n)


class TutorialInformationPageBlockFactory(DjangoModelFactory):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = TutorialInformationPageBlock

    client_id = factory.LazyFunction(lambda: str(ULID()))
    block_number = factory.Sequence(lambda n: n)

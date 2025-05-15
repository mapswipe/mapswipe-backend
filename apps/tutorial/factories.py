import factory
from factory.django import DjangoModelFactory
from ulid import ULID

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

    client_id = factory.LazyFunction(lambda: str(ULID()))
    # name = factory.Sequence(lambda n: f"Tutorial {n}")


class TutorialScenarioPageFactory(DjangoModelFactory):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = TutorialScenarioPage

    client_id = factory.LazyFunction(lambda: str(ULID()))
    scenario_id = factory.Sequence(lambda n: n)


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

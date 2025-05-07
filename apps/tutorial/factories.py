import factory
from factory.django import DjangoModelFactory

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

    name = factory.Sequence(lambda n: f"Organization {n}")


class TutorialScenarioPageFactory(DjangoModelFactory):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = TutorialScenarioPage

    scenario_id = factory.Sequence(lambda n: n)


class TutorialTaskFactory(DjangoModelFactory):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = TutorialTask

    reference = 1
    project_type_specifics = factory.LazyAttribute(lambda _: {})


class TutorialInformationPageFactory(DjangoModelFactory):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = TutorialInformationPage

    title = factory.Sequence(lambda n: f"Page {n}")
    page_number = factory.Sequence(lambda n: n)


class TutorialInformationPageBlockFactory(DjangoModelFactory):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = TutorialInformationPageBlock

    block_number = factory.Sequence(lambda n: n)

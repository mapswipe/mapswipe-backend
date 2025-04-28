import factory
from factory.django import DjangoModelFactory

from .models import (
    Organization,
    Project,
    ProjectTask,
    ProjectTaskGroup,
)


class OrganizationFactory(DjangoModelFactory):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Organization

    name = factory.Sequence(lambda n: f"Organization {n}")


class ProjectFactory(DjangoModelFactory):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Project

    name = factory.Sequence(lambda n: f"Project {n}")

    project_type = Project.Type.FIND
    project_type_specifics = None

    look_for = "Buildings and Roads"
    description = "We want to identify buildings and roads"


class TaskGroupFactory(DjangoModelFactory):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = ProjectTaskGroup

    project_type_specifics = factory.LazyAttribute(lambda _: {})
    number_of_tasks = 100
    required_count = 50

    finished_count = 50
    progress = 50

    total_area = 100
    time_spent_max_allowed = 1


class TaskFactory(DjangoModelFactory):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = ProjectTask

    project_type_specifics = factory.LazyAttribute(lambda _: {})

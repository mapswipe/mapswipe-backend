# pyright: reportRedeclaration=false
# pyright: reportIncompatibleVariableOverride=false
# pyright: reportMissingTypeArgument=false
import typing

import factory
from django.contrib.gis.geos import Point
from factory.django import DjangoModelFactory
from ulid import ULID

from .models import (
    Organization,
    Project,
    ProjectTask,
    ProjectTaskGroup,
)


class OrganizationFactory(DjangoModelFactory):
    class Meta:
        model = Organization

    client_id = factory.LazyFunction(lambda: str(ULID()))
    name = factory.Sequence(lambda n: f"Organization {n}")
    description = "Test description"


class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project

    client_id = factory.LazyFunction(lambda: str(ULID()))
    name = factory.Sequence(lambda n: f"Project {n}")

    project_type = Project.Type.FIND
    project_type_specifics = None

    look_for = "Buildings and Roads"
    description = "We want to identify buildings and roads"

    centroid = Point(1, 2)


class ProjectTaskGroupFactory(DjangoModelFactory):
    class Meta:
        model = ProjectTaskGroup

    project_type_specifics = factory.LazyAttribute(lambda _: {})
    number_of_tasks = 100
    required_count = 50

    finished_count = 50
    progress = 50

    total_area = 100
    time_spent_max_allowed = 1


class ProjectTaskFactory(DjangoModelFactory):
    class Meta:
        model = ProjectTask

    project_type_specifics = factory.LazyAttribute(lambda _: {})


# NOTE: Make sure to add type hints for each factory class defined above
# NOTE: This needs to be at the end of this file
if typing.TYPE_CHECKING:
    OrganizationFactory: type[DjangoModelFactory[Organization]]
    ProjectFactory: type[DjangoModelFactory[Project]]
    ProjectTaskGroupFactory: type[DjangoModelFactory[ProjectTaskGroup]]
    ProjectTaskFactory: type[DjangoModelFactory[ProjectTask]]

# pyright: reportRedeclaration=false
# pyright: reportIncompatibleVariableOverride=false
# pyright: reportMissingTypeArgument=false
import typing
import uuid

import factory
from factory.django import DjangoModelFactory
from ulid import ULID

from .models import (
    ContributorTeam,
    ContributorUser,
    ContributorUserGroup,
    ContributorUserGroupMembership,
    ContributorUserGroupMembershipLog,
)


class ContributorUserFactory(DjangoModelFactory):
    class Meta:
        model = ContributorUser

    user_id = factory.LazyAttribute(lambda _: f"contributor-user-id-{uuid.uuid4().int % 1000000}")
    username = factory.Sequence(lambda n: f"Contributor User {n}")


class ContributorUserGroupFactory(DjangoModelFactory):
    class Meta:
        model = ContributorUserGroup

    client_id = factory.LazyFunction(lambda: str(ULID()))
    name = factory.Sequence(lambda n: f"Contributor User Group {n}")
    description = "Some description"


class ContributorUserGroupMembershipFactory(DjangoModelFactory):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = ContributorUserGroupMembership

    # NOTE: We can't set default=True in the model because this attribute must be explicitly specified during creation.
    # The state is managed at the Firebase level.
    is_active = True


class ContributorUserGroupMembershipLogFactory(DjangoModelFactory):
    class Meta:
        model = ContributorUserGroupMembershipLog


class ContributorTeamFactory(DjangoModelFactory):
    class Meta:
        model = ContributorTeam

    client_id = factory.LazyFunction(lambda: str(ULID()))
    name = factory.Sequence(lambda n: f"Contributor User Team {n}")


# NOTE: Make sure to add type hints for each factory class defined below
# NOTE: This needs to be at the end of this file
if typing.TYPE_CHECKING:
    ContributorUserFactory: type[DjangoModelFactory[ContributorUser]]
    ContributorTeamFactory: type[DjangoModelFactory[ContributorTeam]]
    ContributorUserGroupFactory: type[DjangoModelFactory[ContributorUserGroup]]
    ContributorUserGroupMembershipFactory: type[DjangoModelFactory[ContributorUserGroupMembership]]
    ContributorUserGroupMembershipLogFactory: type[DjangoModelFactory[ContributorUserGroupMembershipLog]]

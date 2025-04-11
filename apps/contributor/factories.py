import factory
from factory.django import DjangoModelFactory

from .models import (
    ContributorUser,
    ContributorUserGroup,
    ContributorUserGroupMembership,
    ContributorUserGroupMembershipLog,
)


class ContributorUserFactory(DjangoModelFactory):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = ContributorUser

    user_id = factory.Sequence(lambda n: f"Contributor User {n}")
    username = factory.Sequence(lambda n: f"Contributor User {n}")


class ContributorUserGroupFactory(DjangoModelFactory):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = ContributorUserGroup

    name = factory.Sequence(lambda n: f"Contributor User Group {n}")
    description = "Some description"


class ContributorUserGroupMembershipFactory(DjangoModelFactory):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = ContributorUserGroupMembership


class ContributorUserGroupMembershipLogFactory(DjangoModelFactory):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = ContributorUserGroupMembershipLog

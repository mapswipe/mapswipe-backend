# pyright: reportUninitializedInstanceVariable=false
import typing

from django.db import models
from django_choices_field import IntegerChoicesField

from apps.common.models import ArchivableResource, UserResource


# NOTE: Users are created from Apps (Web/Mobile)
class ContributorUser(models.Model):
    # NOTE: Sync with firebase
    user_id = models.CharField(
        max_length=30,
        db_index=True,
        unique=True,
        help_text="Firebase User ID",
    )
    team = models.ForeignKey(
        "ContributorTeam",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user",
    )
    username = models.CharField(max_length=255)
    created_at = models.DateTimeField(null=True)
    modified_at = models.DateTimeField(null=True)

    @typing.override
    def __str__(self):
        return self.username


class ContributorUserGroup(ArchivableResource, UserResource):  # type: ignore[reportIncompatibleVariableOverride]
    old_id = models.CharField(max_length=30, db_index=True, null=True)
    name = models.CharField(max_length=255)
    description = models.TextField()

    @typing.override
    def __str__(self):
        return self.name


class ContributorUserGroupMembership(models.Model):
    user_group = models.ForeignKey(ContributorUserGroup, on_delete=models.CASCADE)
    user = models.ForeignKey(ContributorUser, on_delete=models.CASCADE)
    is_active = models.BooleanField()

    # Type hints
    user_group_id: int
    user_id: int

    @typing.override
    def __str__(self):
        return f"user_group_id={self.user_group_id}, user_id={self.user_id}, is_active={self.is_active}"


class ContributorUserGroupMembershipLogActionEnum(models.IntegerChoices):
    JOIN = 1, "Join"
    LEAVE = 2, "Leave"


class ContributorUserGroupMembershipLog(models.Model):
    ACTION = ContributorUserGroupMembershipLogActionEnum

    membership = models.ForeignKey(ContributorUserGroupMembership, on_delete=models.CASCADE)
    # Sync with firebase
    action = IntegerChoicesField(choices_enum=ContributorUserGroupMembershipLogActionEnum)
    date = models.DateTimeField()

    # Type hints
    membership_id: int

    @typing.override
    def __str__(self):
        return f"membership={self.membership_id}, action={self.action}"


# TEAM
class ContributorTeam(ArchivableResource, UserResource):  # type: ignore[reportIncompatibleVariableOverride]
    name = models.CharField(max_length=255)

    @typing.override
    def __str__(self):
        return self.name

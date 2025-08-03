# pyright: reportUninitializedInstanceVariable=false
import typing
import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext
from django_choices_field import IntegerChoicesField

from apps.common.models import ArchivableResource, FirebasePushResource, UserResource


# NOTE: Users are created from Apps (Web/Mobile)
class ContributorUser(FirebasePushResource):
    team: "ContributorTeam | None" = models.ForeignKey(  # type: ignore[reportIncompatibleVariableOverride]
        "ContributorTeam",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user",
    )

    # NOTE: From firebase
    username = models.CharField(max_length=255)
    firebase_id = models.CharField(
        max_length=30,
        unique=True,
        help_text="Firebase User ID (External)",
    )
    created_at = models.DateTimeField(null=True)
    modified_at = models.DateTimeField(null=True)

    @typing.override
    def __str__(self):
        return self.username


class ContributorUserGroup(ArchivableResource, UserResource, FirebasePushResource):  # type: ignore[reportIncompatibleVariableOverride]
    name = models.CharField(max_length=255)
    description = models.TextField()

    @typing.override
    def __str__(self):
        return self.name


# NOTE: Extend FirebasePullResource later if necessary
class ContributorUserGroupMembership(models.Model):
    user_group: ContributorUserGroup = models.ForeignKey(ContributorUserGroup, on_delete=models.CASCADE)  # type: ignore[reportIncompatibleVariableOverride]
    user: ContributorUser = models.ForeignKey(ContributorUser, on_delete=models.CASCADE)  # type: ignore[reportIncompatibleVariableOverride]
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

    membership: ContributorUserGroupMembership = models.ForeignKey(ContributorUserGroupMembership, on_delete=models.CASCADE)  # type: ignore[reportIncompatibleVariableOverride]
    # Sync with firebase
    action = IntegerChoicesField(choices_enum=ContributorUserGroupMembershipLogActionEnum)
    date = models.DateTimeField()

    # Type hints
    membership_id: int

    @typing.override
    def __str__(self):
        return f"membership={self.membership_id}, action={self.action}"


# TEAM
class ContributorTeam(ArchivableResource, UserResource, FirebasePushResource):  # type: ignore[reportIncompatibleVariableOverride]
    name = models.CharField(max_length=255)
    token = models.UUIDField(default=uuid.uuid4, unique=True)

    @typing.override
    def __str__(self):
        return self.name

    @typing.override
    def clean(self):
        super().clean()
        if self.pk and self.is_archived and ContributorUser.objects.filter(team_id=self.pk).exists():
            raise ValidationError(
                {"is_archived": gettext("Cannot archive a team that still has team members.")},
            )

# pyright: reportUninitializedInstanceVariable=false
import datetime
import typing
import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext
from django_choices_field import IntegerChoicesField

from apps.common.models import ArchivableResource, FirebasePushResource, UserResource


# NOTE: Users are created from Apps (Web/Mobile)
class ContributorUser(FirebasePushResource):
    """Model representing contributors synchronized from firebase.

    Contributor accounts are typically created in firebase and then synced into this system.
    A contributor user may or may not be linked to a corresponding user in the system.
    """

    team = models.ForeignKey["ContributorTeam | None", "ContributorTeam | None"](
        "ContributorTeam",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user",
    )

    # NOTE: From firebase
    username = models.CharField[str, str](max_length=255)
    firebase_id = models.CharField[str, str](
        max_length=30,
        unique=True,
        help_text="Firebase User ID (External)",
    )
    created_at = models.DateTimeField[datetime.datetime | None, datetime.datetime | None](null=True)
    modified_at = models.DateTimeField[datetime.datetime | None, datetime.datetime | None](null=True)

    # Type hints
    id: int

    @typing.override
    def __str__(self):
        return self.username

    @typing.override
    def clean(self):
        super().clean()
        if self.team and self.team.is_archived:
            raise ValidationError(
                {"team": gettext("Cannot create or update member to archived team.")},
            )


class ContributorUserGroup(ArchivableResource, UserResource, FirebasePushResource):  # type: ignore[reportIncompatibleVariableOverride]
    """Model representing a group that contributor users can join or leave.

    Groups are used to aggregate contributions made by users within the group,
    facilitating management and organization of collective efforts.
    """

    name = models.CharField[str, str](max_length=255)
    description = models.TextField[str, str]()

    @typing.override
    def __str__(self):
        return self.name


# NOTE: Extend FirebasePullResource later if necessary
class ContributorUserGroupMembership(models.Model):
    """Model representing membership of contributor users in contributor user groups."""

    user_group = models.ForeignKey[ContributorUserGroup, ContributorUserGroup](
        ContributorUserGroup,
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey[ContributorUser, ContributorUser](ContributorUser, on_delete=models.CASCADE)
    is_active = models.BooleanField[bool, bool]()

    # Type hints
    user_group_id: int
    user_id: int

    class Meta:
        unique_together = (
            "user_group",
            "user",
        )

    @typing.override
    def __str__(self):
        return f"user_group_id={self.user_group_id}, user_id={self.user_id}, is_active={self.is_active}"


class ContributorUserGroupMembershipLogActionEnum(models.IntegerChoices):
    """Model representing membership action for contributor users."""

    JOIN = 1, "Join"
    LEAVE = 2, "Leave"


class ContributorUserGroupMembershipLog(models.Model):
    """Model representing membership logs for contributor user such as joining or leaving groups."""

    ACTION = ContributorUserGroupMembershipLogActionEnum

    membership = models.ForeignKey[ContributorUserGroupMembership, ContributorUserGroupMembership](
        ContributorUserGroupMembership,
        on_delete=models.CASCADE,
    )
    # Sync with firebase
    action: int = IntegerChoicesField(choices_enum=ContributorUserGroupMembershipLogActionEnum)  # type: ignore[reportAssignmentType]
    date = models.DateTimeField[datetime.date, datetime.date]()

    # Type hints
    membership_id: int

    @typing.override
    def __str__(self):
        return f"membership={self.membership_id}, action={self.action}"


# TEAM
class ContributorTeam(ArchivableResource, UserResource, FirebasePushResource):  # type: ignore[reportIncompatibleVariableOverride]
    """Model representing a private team that contributor users can be assigned to.

    Team membership is managed exclusively by system managers; contributor users
    cannot join or leave teams on their own. Members of a team can only access
    projects linked to that team.
    """

    name = models.CharField[str, str](max_length=255)
    token = models.UUIDField(default=uuid.uuid4, unique=True)

    @typing.override
    def __str__(self):
        return f"Archived - {self.name}" if self.is_archived else self.name

    @typing.override
    def clean(self):
        super().clean()
        if self.pk and self.is_archived and ContributorUser.objects.filter(team_id=self.pk).exists():
            raise ValidationError(
                {"is_archived": gettext("Cannot archive a team that still has team members.")},
            )

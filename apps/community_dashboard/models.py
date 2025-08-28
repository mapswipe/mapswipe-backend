# pyright: reportUninitializedInstanceVariable=false
import datetime
import typing

from django.db import models
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django_choices_field import IntegerChoicesField

from apps.contributor.models import ContributorUser, ContributorUserGroup
from apps.project.models import Project
from main.db import Model


class AggregatedTrackingTypeEnum(models.IntegerChoices):
    USER_DATA_LATEST_DATE = 0, _("Contributor User Data Latest Date")
    USER_GROUP_DATA_LATEST_DATE = 1, _("Contributor UserGroup Stat Data Latest Date")


class AggregatedTracking(Model):
    type: int = IntegerChoicesField(choices_enum=AggregatedTrackingTypeEnum, unique=True)  # type: ignore[reportAssignmentType]
    updated_at = models.DateTimeField[datetime.datetime, datetime.datetime](auto_now=True)
    # TODO(thenav56): Change the value to DateField
    value = models.CharField[str | None, str | None](
        max_length=225,
        null=True,
        help_text=gettext("Represents the date before which data is synced to aggregated tables."),
    )

    @typing.override
    def __str__(self):
        return f"{self.type=}, {self.updated_at=}, {self.value=}"


class AggregatedUserStatData(Model):
    # Ref Fields
    project = models.ForeignKey[Project, Project](Project, on_delete=models.CASCADE, related_name="+")
    user = models.ForeignKey[ContributorUser, ContributorUser](ContributorUser, on_delete=models.CASCADE, related_name="+")
    timestamp_date = models.DateField[datetime.date, datetime.date]()
    # Aggregated Fields
    total_time = models.IntegerField[int, int]()  # seconds
    task_count = models.IntegerField[int, int]()  # Number of tasks
    swipes = models.IntegerField[int, int]()  # Number of swipes
    area_swiped = models.FloatField[float, float]()  # sqkm

    # Type hints
    project_id: int
    user_id: int

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        unique_together = (
            "project",
            "user",
            "timestamp_date",
        )

    @typing.override
    def __str__(self):
        return f"{self.project_id=}, {self.user_id=}"


class AggregatedUserGroupStatData(Model):
    # Ref Fields
    project = models.ForeignKey[Project, Project](Project, on_delete=models.CASCADE, related_name="+")
    user = models.ForeignKey[ContributorUser, ContributorUser](ContributorUser, on_delete=models.CASCADE, related_name="+")
    user_group = models.ForeignKey[ContributorUserGroup, ContributorUserGroup](
        ContributorUserGroup,
        on_delete=models.CASCADE,
        related_name="+",
    )
    timestamp_date = models.DateField[datetime.date, datetime.date]()
    # Aggregated Fields
    total_time = models.IntegerField[int, int]()  # seconds
    task_count = models.FloatField[float, float]()  # Number of tasks
    swipes = models.FloatField[float, float]()  # Number of swipes
    area_swiped = models.FloatField[float, float]()

    # Type hints
    project_id: int
    user_id: int
    user_group_id: int

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        unique_together = (
            "project",
            "user",
            "user_group",
            "timestamp_date",
        )

    @typing.override
    def __str__(self):
        return f"{self.project_id=}, {self.user_id=}, {self.user_group_id=}"

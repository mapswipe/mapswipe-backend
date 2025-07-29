# pyright: reportUninitializedInstanceVariable=false
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
    type = IntegerChoicesField(choices_enum=AggregatedTrackingTypeEnum, unique=True)
    updated_at = models.DateTimeField(auto_now=True)
    value = models.CharField(
        max_length=225,
        null=True,
        help_text=gettext("Represents the date before which data is synced to aggregated tables."),
    )

    @typing.override
    def __str__(self):
        return f"{self.type=}, {self.updated_at=}, {self.value=}"


class AggregatedUserStatData(Model):
    # Ref Fields
    project: Project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="+")  # type: ignore[reportIncompatibleVariableOverride]
    user: ContributorUser = models.ForeignKey(ContributorUser, on_delete=models.CASCADE, related_name="+")  # type: ignore[reportIncompatibleVariableOverride]
    timestamp_date = models.DateField()
    # Aggregated Fields
    total_time = models.IntegerField()  # seconds
    task_count = models.IntegerField()  # Number of tasks
    swipes = models.IntegerField()  # Number of swipes
    area_swiped = models.FloatField()  # sqkm

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
    project: Project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="+")  # type: ignore[reportIncompatibleVariableOverride]
    user: ContributorUser = models.ForeignKey(ContributorUser, on_delete=models.CASCADE, related_name="+")  # type: ignore[reportIncompatibleVariableOverride]
    user_group: ContributorUserGroup = models.ForeignKey(ContributorUserGroup, on_delete=models.CASCADE, related_name="+")  # type: ignore[reportIncompatibleVariableOverride]
    timestamp_date = models.DateField()
    # Aggregated Fields
    total_time = models.IntegerField()  # seconds
    task_count = models.FloatField()  # Number of tasks
    swipes = models.FloatField()  # Number of swipes
    area_swiped = models.FloatField()

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

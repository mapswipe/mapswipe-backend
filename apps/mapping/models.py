# pyright: reportUninitializedInstanceVariable=false
# TODO(thenav56): Check and add missing unique_together
import typing

from django.db import models
from django_choices_field import IntegerChoicesField

from apps.contributor.models import ContributorUser, ContributorUserGroup
from apps.project.models import ProjectTask, ProjectTaskGroup


class MappingSessionClientTypeEnum(models.IntegerChoices):
    UNKNOWN = 0, "Unknown"
    MOBILE_ANDROID = 1, "Mobile (Android)"
    MOBILE_IOS = 2, "Mobile (IOS)"
    WEB = 3, "Web"

    @classmethod
    def get_client_type(cls, value: str) -> "MappingSessionClientTypeEnum":
        return {
            "mobile-android": cls.MOBILE_ANDROID,
            "mobile-ios": cls.MOBILE_IOS,
            "web": cls.WEB,
        }.get(value, cls.UNKNOWN)


class MappingSession(models.Model):
    project_task_group: ProjectTaskGroup = models.ForeignKey(ProjectTaskGroup, on_delete=models.PROTECT)  # type: ignore[reportIncompatibleVariableOverride]
    contributor_user: ContributorUser = models.ForeignKey(ContributorUser, on_delete=models.PROTECT)  # type: ignore[reportIncompatibleVariableOverride]

    app_version = models.CharField(max_length=10)
    client_type = IntegerChoicesField(choices_enum=MappingSessionClientTypeEnum)
    items_count = models.IntegerField()  # TODO(thenav56): Rename or just use task_group.number_of_tasks?
    start_time = models.DateTimeField(null=True, blank=True)  # XXX: New data are not null
    end_time = models.DateTimeField(null=True, blank=True)  # XXX: New data are not null

    # Type hints
    id: int
    project_task_group_id: int
    contributor_user_id: int

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        unique_together = (("project_task_group", "contributor_user"),)

    @typing.override
    def __str__(self):
        return str(self.pk)


class MappingSessionUserGroup(models.Model):
    mapping_session: MappingSession = models.ForeignKey(MappingSession, on_delete=models.PROTECT)  # type: ignore[reportIncompatibleVariableOverride]
    user_group: ContributorUserGroup = models.ForeignKey(  # type: ignore[reportIncompatibleVariableOverride]
        ContributorUserGroup,
        on_delete=models.PROTECT,
        related_name="+",
    )

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        unique_together = (("mapping_session", "user_group"),)

    @typing.override
    def __str__(self):
        return str(self.pk)


class MappingSessionResult(models.Model):
    session: MappingSession = models.ForeignKey(MappingSession, on_delete=models.PROTECT)  # type: ignore[reportIncompatibleVariableOverride]
    project_task: ProjectTask = models.ForeignKey(ProjectTask, on_delete=models.PROTECT)  # type: ignore[reportIncompatibleVariableOverride]
    result = models.PositiveSmallIntegerField()

    # TODO(thenav56): Add constraint to make sure we have non-duplicate row with task_id, .session.user_id

    # Type hints
    session_id: int
    project_task_id: int

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        unique_together = (("session", "project_task"),)

    @typing.override
    def __str__(self):
        return str(self.pk)


# TODO: Rename to MappingSessionUserGroupStage?
class MappingSessionUserGroupTemp(models.Model):
    project_firebase_id = models.CharField(max_length=255)
    group_firebase_id = models.CharField(max_length=255)
    contributor_user_firebase_id = models.CharField(max_length=255)
    user_group_firebase_id = models.CharField(max_length=255)

    @typing.override
    def __str__(self):
        return str(self.pk)


# TODO: Rename to MappingSessionResultStage?
class MappingSessionResultTemp(models.Model):
    project_firebase_id = models.CharField(max_length=255)
    group_firebase_id = models.CharField(max_length=255)
    contributor_user_firebase_id = models.CharField(max_length=255)
    task_firebase_id = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    result = models.PositiveSmallIntegerField()
    app_version = models.CharField(max_length=255)
    client_type = IntegerChoicesField(choices_enum=MappingSessionClientTypeEnum)

    @typing.override
    def __str__(self):
        return str(self.pk)


# TODO(thenav56): mapping_sessions_results_geometry (This was used for DIGITIZATION)
#
# CREATE TABLE IF NOT EXISTS mapping_sessions_results_geometry (
#     mapping_session_id int8,
#     task_id varchar,
#     result geometry not null,
#     PRIMARY KEY (mapping_session_id, task_id),
#     FOREIGN KEY (mapping_session_id)
#     references mapping_sessions (mapping_session_id)
# );

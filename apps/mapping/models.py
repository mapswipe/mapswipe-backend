from django.db import models
from django_choices_field import IntegerChoicesField

from apps.contributor.models import ContributorUser
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
    project_task_group = models.ForeignKey(ProjectTaskGroup, on_delete=models.PROTECT)
    contributor_user = models.ForeignKey(ContributorUser, on_delete=models.PROTECT)

    app_version = models.CharField(max_length=10)
    client_type = IntegerChoicesField(choices_enum=MappingSessionClientTypeEnum)
    items_count = models.IntegerField()  # TODO: Rename or just use task_group.number_of_tasks?
    start_time = models.DateTimeField(null=True, blank=True)  # XXX: New data are not null
    end_time = models.DateTimeField(null=True, blank=True)  # XXX: New data are not null

    def __str__(self):
        return str(self.pk)


class MappingSessionResult(models.Model):
    session = models.ForeignKey(MappingSession, on_delete=models.PROTECT)
    project_task = models.ForeignKey(ProjectTask, on_delete=models.PROTECT)
    result = models.PositiveSmallIntegerField()

    # TODO: Add constrant to make sure we have non-duplicate row with task_id, .session.user_id

    def __str__(self):
        return str(self.pk)


# TODO: mapping_sessions_results_geometry
#
# CREATE TABLE IF NOT EXISTS mapping_sessions_results_geometry (
#     mapping_session_id int8,
#     task_id varchar,
#     result geometry not null,
#     PRIMARY KEY (mapping_session_id, task_id),
#     FOREIGN KEY (mapping_session_id)
#     references mapping_sessions (mapping_session_id)
# );

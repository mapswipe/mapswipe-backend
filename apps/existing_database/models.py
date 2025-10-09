# pyright: reportUninitializedInstanceVariable=false
# pyright: reportIncompatibleVariableOverride=false
# ruff: noqa: D101
import datetime
import typing

from django.contrib.gis.db import models as gis_models
from django.db import models

from main.db import Model

# NOTE: Django model definition and existing table structure doesn't entirely matches.
# This is to be used for data migration only.


class User(Model):
    user_id = models.CharField[str, str](primary_key=True, max_length=999)
    username = models.CharField[str | None, str | None](max_length=999, blank=True, null=True)
    created = models.DateTimeField[datetime.datetime, datetime.datetime]()
    updated_at = models.DateTimeField[datetime.datetime, datetime.datetime]()

    class Meta:
        managed = False
        db_table = "users"

    @typing.override
    def __str__(self):
        return f"{self.user_id}: {self.username}"


class UserGroup(Model):
    user_group_id = models.CharField[str, str](primary_key=True, max_length=999)
    name = models.CharField[str | None, str | None](max_length=999, null=True)
    description = models.TextField[str | None, str | None](blank=True, null=True)
    created_at = models.DateTimeField[datetime.datetime | None, datetime.datetime | None](blank=True, null=True)
    created_by = models.ForeignKey[User, User](User, models.DO_NOTHING, related_name="+")
    archived_at = models.DateTimeField[datetime.datetime | None, datetime.datetime | None](blank=True, null=True)
    archived_by = models.ForeignKey[User, User](User, models.DO_NOTHING, related_name="+")
    is_archived = models.BooleanField[bool | None, bool | None](blank=True, null=True)

    # type hints
    created_by_id: str
    archived_by_id: str | None

    class Meta:
        managed = False
        db_table = "user_groups"

    @typing.override
    def __str__(self):
        return self.user_group_id

    def user_memberships(self):
        return UserGroupUserMembership.objects.filter(user_group_id=self.user_group_id).select_related("user")


class UserGroupUserMembership(Model):
    pk = models.CompositePrimaryKey("user_group", "user")
    user_group = models.ForeignKey[UserGroup, UserGroup](UserGroup, models.DO_NOTHING, related_name="+")
    user = models.ForeignKey[User, User](User, models.DO_NOTHING, related_name="+")
    is_active = models.BooleanField[bool, bool](default=True)

    # Django derived fields from ForeignKey
    user_id: str
    user_group_id: str

    class Meta:
        managed = False
        db_table = "user_groups_user_memberships"
        unique_together = (("user_group", "user"),)

    @typing.override
    def __str__(self):
        return f"UG:{self.user_group_id}-U:{self.user_id}"


class Project(Model):
    class Type(models.IntegerChoices):
        BUILD_AREA = 1, "Find"
        FOOTPRINT = 2, "Validate"
        CHANGE_DETECTION = 3, "Compare"
        COMPLETENESS = 4, "Completeness"
        MEDIA = 5, "Media"
        DIGITIZATION = 6, "Digitization"
        STREET = 7, "Street"

    project_id = models.CharField[str, str](primary_key=True, max_length=999)
    created = models.DateTimeField[datetime.datetime | None, datetime.datetime | None](blank=True, null=True)
    created_by = models.CharField[str | None, str | None](max_length=999, blank=True, null=True)
    geom = gis_models.GeometryField(blank=True, null=True)
    image = models.CharField[str | None, str | None](max_length=999, blank=True, null=True)
    is_featured = models.BooleanField[bool | None, bool | None](blank=True, null=True)
    look_for = models.CharField[str | None, str | None](max_length=999, blank=True, null=True)
    name = models.CharField[str | None, str | None](max_length=999, blank=True, null=True)
    progress = models.IntegerField[int | None, int | None](blank=True, null=True)
    project_details = models.CharField[str | None, str | None](max_length=999, blank=True, null=True)
    project_type = models.IntegerField[int | None, int | None](choices=Type.choices, blank=True, null=True)
    required_results = models.IntegerField[int | None, int | None](blank=True, null=True)
    result_count = models.IntegerField[int | None, int | None](blank=True, null=True)
    status = models.CharField[str | None, str | None](max_length=999, blank=True, null=True)
    verification_number = models.IntegerField[int | None, int | None](blank=True, null=True)
    # Database uses JSON instead of JSONB (not supported by django)
    project_type_specifics = models.TextField[
        dict[typing.Any, typing.Any] | None,
        dict[typing.Any, typing.Any] | None,
    ](blank=True, null=True)
    organization_name = models.CharField[str | None, str | None](max_length=1000, null=True, blank=True)

    # type hints
    created_by_id: int

    class Meta:
        managed = False
        db_table = "projects"

    @typing.override
    def __str__(self):
        return self.project_id


class Group(Model):
    pk = models.CompositePrimaryKey("project_id", "group_id")
    group_id = models.CharField[str, str](max_length=999)
    project = models.ForeignKey["Project", "Project"]("Project", models.DO_NOTHING, related_name="+")
    number_of_tasks = models.IntegerField[int | None, int | None](blank=True, null=True)
    finished_count = models.IntegerField[int | None, int | None](blank=True, null=True)
    required_count = models.IntegerField[int | None, int | None](blank=True, null=True)
    progress = models.IntegerField[int | None, int | None](blank=True, null=True)
    # Database uses JSON instead of JSONB (not supported by django)
    project_type_specifics = models.TextField[str | None, str | None](blank=True, null=True, default=None)
    # Used by aggreagated module
    total_area = models.FloatField[float | None, float | None](blank=True, null=True, default=None)
    time_spent_max_allowed = models.FloatField[float | None, float | None](blank=True, null=True, default=None)

    # Django derived fields from ForeignKey
    project_id: str

    class Meta:
        managed = False
        db_table = "groups"
        unique_together = (("project", "group_id"),)

    @typing.override
    def __str__(self):
        return f"P:{self.project_id}-G:{self.group_id}"


class Task(Model):
    # NOTE: Primary Key: project_id, group_id, tasks_id
    pk = models.CompositePrimaryKey("project_id", "group_id", "task_id")
    project = models.ForeignKey[Project, Project](Project, models.DO_NOTHING, related_name="+")
    group_id = models.CharField[str, str](max_length=999)
    task_id = models.CharField[str, str](max_length=999)
    geom = gis_models.GeometryField(blank=True, null=True)
    # Database uses JSON instead of JSONB (not supported by django)
    project_type_specifics = models.TextField[str | None, str | None](blank=True, null=True)

    # Django derived fields from ForeignKey
    project_id: str

    class Meta:
        managed = False
        db_table = "tasks"
        unique_together = (("project", "group_id", "task_id"),)

    @property
    def group(self):
        return Group.objects.filter(project=self.project, group_id=self.group_id).first()

    @typing.override
    def __str__(self):
        return f"P:{self.project_id}-G:{self.group_id}-T:{self.task_id}"


class Result(Model):
    # NOTE: Primary Key: project_id, group_id, tasks_id, user_id
    pk = models.CompositePrimaryKey("project_id", "group_id", "task_id", "user_id")
    project = models.ForeignKey[Project, Project](Project, models.DO_NOTHING, related_name="+")
    group_id = models.CharField[str, str](max_length=999)
    task_id = models.CharField[str, str](max_length=999)
    user = models.ForeignKey[User, User](User, models.DO_NOTHING, related_name="+")
    timestamp = models.DateTimeField[datetime.datetime | None, datetime.datetime | None](blank=True, null=True)
    start_time = models.DateTimeField[datetime.datetime | None, datetime.datetime | None](blank=True, null=True)
    end_time = models.DateTimeField[datetime.datetime | None, datetime.datetime | None](blank=True, null=True)
    result = models.SmallIntegerField[int | None, int | None](blank=True, null=True)

    # Django derived fields from ForeignKey
    project_id: str
    user_id: str

    class Meta:
        managed = False
        db_table = "results"
        unique_together = (("project", "group_id", "task_id", "user"),)

    @typing.override
    def __str__(self):
        return f"P:{self.project_id}-G:{self.group_id}-T:{self.task_id}-U:{self.user_id}"

    @property
    def group(self):
        return Group.objects.filter(
            project=self.project,
            group_id=self.group_id,
        ).first()

    @property
    def task(self):
        return Task.objects.filter(
            project=self.project,
            group_id=self.group_id,
            task_id=self.task_id,
        ).first()


class UserGroupResult(Model):
    pk = models.CompositePrimaryKey("project_id", "group_id", "user_id", "user_group")
    project = models.ForeignKey[Project, Project](Project, on_delete=models.DO_NOTHING, related_name="+")
    group_id = models.CharField[str, str](max_length=999)
    user = models.ForeignKey[User, User](User, on_delete=models.DO_NOTHING, related_name="+")
    user_group = models.ForeignKey[UserGroup, UserGroup](UserGroup, on_delete=models.DO_NOTHING, related_name="+")

    # Django derived fields from ForeignKey
    project_id: str
    user_id: str
    user_group_id: str

    class Meta:
        managed = False
        db_table = "results_user_groups"
        unique_together = (("project", "group_id", "user_id", "user_group"),)

    @typing.override
    def __str__(self):
        return f"P:{self.project_id}-G:{self.group_id}-UG:{{self.user_group_id}}-U:{{self.user_id}}"

    @property
    def group(self):
        return Group.objects.filter(
            project=self.project,
            group_id=self.group_id,
        ).first()


# New Mapping sessions tables
class MappingSession(Model):
    # This should be primary key instead
    mapping_session_id = models.BigAutoField[int, int](primary_key=True)
    # NOTE: Primary Key: project_id, group_id, tasks_id, user_id
    project = models.ForeignKey[Project, Project](Project, models.DO_NOTHING, related_name="+")
    group_id = models.CharField[str, str](max_length=999)
    user = models.ForeignKey[User, User](User, models.DO_NOTHING, related_name="+")
    start_time = models.DateTimeField[datetime.datetime | None, datetime.datetime | None](blank=True, null=True)
    end_time = models.DateTimeField[datetime.datetime | None, datetime.datetime | None](blank=True, null=True)
    items_count = models.SmallIntegerField[int, int](null=False, default=0)
    app_version = models.CharField[str, str](max_length=999)
    client_type = models.CharField[str, str](max_length=999)

    # Type hints
    project_id: str
    user_id: str

    class Meta:
        managed = False
        db_table = "mapping_sessions"
        unique_together = (("project", "group_id", "user"),)


class MappingSessionResult(Model):
    pk = models.CompositePrimaryKey("mapping_session", "task_id")
    mapping_session = models.ForeignKey[MappingSession, MappingSession](MappingSession, on_delete=models.DO_NOTHING)
    task_id = models.CharField[str, str](max_length=999)
    result = models.SmallIntegerField[int | None, int | None](blank=True, null=True)

    class Meta:
        managed = False
        db_table = "mapping_sessions_results"
        unique_together = (("mapping_session", "task_id"),)


class MappingSessionUserGroup(Model):
    pk = models.CompositePrimaryKey("mapping_session", "user_group")
    mapping_session = models.ForeignKey[MappingSession, MappingSession](MappingSession, on_delete=models.DO_NOTHING)
    user_group = models.ForeignKey[UserGroup, UserGroup](UserGroup, on_delete=models.DO_NOTHING, related_name="+")

    # Type hints
    user_group_id: str
    mapping_session_id: str

    class Meta:
        managed = False
        db_table = "mapping_sessions_user_groups"
        unique_together = (("mapping_session", "user_group"),)


# --- Aggregated dataset tables


class AggregatedTracking(Model):
    class Type(models.IntegerChoices):
        AGGREGATED_USER_STAT_DATA_LATEST_DATE = 0
        AGGREGATED_USER_GROUP_STAT_DATA_LATEST_DATE = 1

    """
    value: represents the date before which data is copied to aggregated tables.
    """
    type = models.IntegerField[int, int](choices=Type.choices, unique=True)
    updated_at = models.DateTimeField[datetime.datetime, datetime.datetime](auto_now=True)
    value = models.CharField[str, str](max_length=225, null=True)

    class Meta:
        managed = False
        db_table = "aggregated_aggregatedtracking"


class AggregatedUserStatData(Model):
    # Ref Fields
    project = models.ForeignKey[Project, Project](Project, on_delete=models.CASCADE, related_name="+")
    user = models.ForeignKey[User, User](User, on_delete=models.CASCADE, related_name="+")
    timestamp_date = models.DateField[datetime.datetime, datetime.datetime]()
    # Aggregated Fields
    total_time = models.IntegerField[int, int]()  # seconds
    task_count = models.IntegerField[int, int]()  # Number of tasks
    swipes = models.IntegerField[int, int]()  # Number of swipes
    area_swiped = models.FloatField[float, float]()  # sqkm

    # Type hints
    user_id: str
    project_id: str

    class Meta:
        managed = False
        db_table = "aggregated_aggregateduserstatdata"
        unique_together = (
            "project",
            "user",
            "timestamp_date",
        )


class AggregatedUserGroupStatData(Model):
    # Ref Fields
    project = models.ForeignKey[Project, Project](Project, on_delete=models.CASCADE, related_name="+")
    user = models.ForeignKey[User, User](User, on_delete=models.CASCADE, related_name="+")
    user_group = models.ForeignKey[UserGroup, UserGroup](
        UserGroup,
        on_delete=models.CASCADE,
        related_name="+",
    )
    timestamp_date = models.DateField[datetime.datetime, datetime.datetime]()
    # Aggregated Fields
    total_time = models.IntegerField[int, int]()  # seconds
    task_count = models.FloatField[float, float]()  # Number of tasks
    swipes = models.FloatField[float, float]()  # Number of swipes
    area_swiped = models.FloatField[float, float]()

    # Type hints
    user_id: str
    project_id: str
    user_group_id: str

    class Meta:
        managed = False
        db_table = "aggregated_aggregatedusergroupstatdata"
        unique_together = (
            "project",
            "user",
            "user_group",
            "timestamp_date",
        )

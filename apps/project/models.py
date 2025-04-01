import typing

from django.contrib.gis.db import models as gid_models
from django.db import models
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy
from django_choices_field import IntegerChoicesField

from apps.common.models import UserResource
from utils.fields import validate_percentage

if typing.TYPE_CHECKING:
    from apps.tutorial.models import Tutorial


class ProjectTypeEnum(models.IntegerChoices):
    BUILD_AREA = 1, "Find"  # Classification
    # FOOTPRINT = 2, "Validate"
    CHANGE_DETECTION = 3, "Compare"
    COMPLETENESS = 4, "Completeness"
    # MEDIA = 5, "Media"
    # DIGITIZATION = 6, "Digitization"
    # STREET = 7, "Street"
    # TODO: Confirm if we have more/less

    @classmethod
    def get_display(cls, value: typing.Self | int) -> str:
        if value in cls:
            return cls(value).label
        return "Unknown"


class ProjectStatusEnum(models.IntegerChoices):
    INACTIVE = 1, "Inactive"
    ACTIVE = 2, "Active"
    PRIVATE_FINISHED = 3, "Private finished"
    ARCHIVED = 4, "Archived"
    FINISHED = 5, "Finished"
    # TODO: Paused?


class UploadHelper:
    @staticmethod
    def project_geometry(instance: "Project", filename):
        return "project/{0}/geometry/{1}".format(instance.pk, filename)

    @staticmethod
    def project_image(instance: "Project", filename):
        return "project/{0}/image/{1}".format(instance.pk, filename)


class Organization(UserResource):
    name = models.CharField(max_length=255)
    unique_name = models.GeneratedField(  # type: ignore[reportAttributeAccessIssue]
        expression=Lower("name"),
        output_field=models.CharField(),
        db_persist=True,
        unique=True,
    )

    def __str__(self):
        return self.name


class Project(UserResource):
    Type = ProjectTypeEnum
    Status = ProjectStatusEnum

    name = models.CharField(max_length=255)
    old_project_id = models.CharField(max_length=30, db_index=True, null=True, blank=True)  # noqa: DJ001
    tutorial: "Tutorial" = models.ForeignKey(  # type: ignore[reportAssignmentType]
        "tutorial.Tutorial",
        null=True,  # NOTE: Validation makes sure active project have tutorial attached
        blank=True,
        on_delete=models.PROTECT,
        related_name="+",
        help_text=gettext_lazy("Tutorial used for this project."),
    )
    is_draft = models.BooleanField(default=True, help_text=gettext_lazy("Draft project can be modified"))
    organization: Organization = models.ForeignKey(  # type: ignore[reportAssignmentType]
        Organization,
        on_delete=models.PROTECT,
        related_name="+",
        help_text=gettext_lazy("Which group, institution or community is requesting this project?"),
    )
    project_type: ProjectTypeEnum = IntegerChoicesField(  # type: ignore[reportAssignmentType]
        choices_enum=ProjectTypeEnum,
    )
    image = models.FileField(upload_to=UploadHelper.project_image)

    # TODO: Currently this field collects any data not stored by another fields, pulled from firebase.
    # Also, used in SQL queries
    # FIXME: Refactor this
    project_type_specifics = models.JSONField(blank=True)

    zoom_level = models.PositiveSmallIntegerField()
    # TODO:t raise CustomError(f"zoom level is too large (max: 22): {zoomLevel}.")
    group_size = models.PositiveSmallIntegerField()
    is_featured = models.BooleanField(default=False)
    look_for = models.CharField(max_length=255, help_text=gettext_lazy("eg: Buildings and Roads"))
    description = models.TextField(null=True, blank=True)  # NOTE: project_details before
    geometry_file = models.FileField(upload_to=UploadHelper.project_geometry, null=True, blank=True)

    progress = models.PositiveSmallIntegerField(default=0, validators=[validate_percentage])
    required_results = models.IntegerField(default=0)
    result_count = models.IntegerField(default=0)  # NOTE: All project have 0 in production database
    status: ProjectStatusEnum = IntegerChoicesField(  # type: ignore[reportAssignmentType]
        choices_enum=ProjectStatusEnum,
        default=ProjectStatusEnum.INACTIVE,
    )

    verification_number = models.PositiveSmallIntegerField()  # TODO: More detail required?

    def __str__(self):
        return self.name

    def update_status(self, status: ProjectStatusEnum, commit=True):
        self.status = status
        if commit:
            self.save(update_fields=("status",))

    def clean(self):
        ...
        # if not self.teamId:
        #     self.status = "inactive"  # this is a public project
        # else:
        #     self.status = (
        #         "private_inactive"  # private project visible only for team members
        #     )
        #
        # if max_tasks_per_user is not None:
        #     self.maxTasksPerUser = int(max_tasks_per_user)

        # for group in self.groups.values():
        #     group.requiredCount = self.verificationNumber
        #     self.requiredResults += group.requiredCount * group.numberOfTasks


class ProjectTaskGroup(models.Model):
    project: Project = models.ForeignKey(  # type: ignore[reportAssignmentType]
        Project,
        on_delete=models.CASCADE,
        related_name="+",
    )

    number_of_tasks = models.IntegerField()
    required_count = models.IntegerField()

    finished_count = models.IntegerField(default=0)
    progress = models.PositiveSmallIntegerField(default=0, validators=[validate_percentage])

    # TODO: Currently this field collects any data not stored by another fields, pulled from firebase.
    # Also, used in SQL queries
    # FIXME: Refactor this
    project_type_specifics = models.JSONField()

    # NOTE: Maintained by Aggregator (Community Dashboard)
    total_area = models.FloatField(null=True, default=None)
    time_spent_max_allowed = models.FloatField(null=True, default=None)

    # Type hints
    project_id: int

    def __str__(self):
        return f"(project={self.project_id}, id={self.pk})"


class ProjectTask(models.Model):
    task_group: ProjectTaskGroup = models.ForeignKey(  # type: ignore[reportAssignmentType]
        ProjectTaskGroup,
        on_delete=models.CASCADE,
        related_name="+",
    )

    # FIXME: Existing gid_models.MultiPolygonField(srid=4326, blank=True, null=True)
    geometry = gid_models.GeometryField(null=True, blank=True, default=None, dim=3)

    # TODO: Currently this field collects any data not stored by another fields, pulled from firebase.
    # Also, used in SQL queries
    # FIXME: Refactor this
    project_type_specifics = models.JSONField()

    # Type hints
    task_group_id: int

    def __str__(self):
        return f"task_group_id={self.task_group_id}, id={self.pk}"

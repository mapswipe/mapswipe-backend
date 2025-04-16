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
    FIND = 1, "Find"
    """ Find project type. Previously known as Classification / Build Area. """

    # FOOTPRINT = 2, "Validate"
    # """ Validate project type. Previously known as Footprint """

    CHANGE_DETECTION = 3, "Compare"
    """ Compare project type. Previously known as Change Detection. """

    COMPLETENESS = 4, "Completeness"
    """ Completeness project type. """

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
    def project_geometry(instance: "Project", filename: str):
        return f"project/{instance.pk}/geometry/{filename}"

    @staticmethod
    def project_image(instance: "Project", filename: str):
        return f"project/{instance.pk}/image/{filename}"


class Organization(UserResource):
    name = models.CharField(max_length=255)
    unique_name = models.GeneratedField(  # type: ignore[reportAttributeAccessIssue]
        expression=Lower("name"),
        output_field=models.CharField(),
        db_persist=True,
        unique=True,
    )

    @typing.override
    def __str__(self) -> str:
        return self.name


class Project(UserResource):
    Type = ProjectTypeEnum
    Status = ProjectStatusEnum

    old_id = models.CharField(max_length=30, db_index=True, null=True, blank=True)  # noqa: DJ001

    project_type: ProjectTypeEnum = IntegerChoicesField(  # type: ignore[reportAssignmentType]
        choices_enum=ProjectTypeEnum,
    )

    # TODO: Should we rename this to requesting_organization
    organization: Organization = models.ForeignKey(  # type: ignore[reportAssignmentType]
        Organization,
        on_delete=models.PROTECT,
        related_name="+",
        help_text=gettext_lazy("Which group, institution or community is requesting this project?"),
    )

    # Generate in manager dashboard based on topic, region, project number, requesting org
    name = models.CharField(max_length=255)

    # TODO: Max length is 25 in manager dashboard.
    look_for = models.CharField(
        max_length=255,
        help_text=gettext_lazy("What should the users look for (e.g. buildings, cars, trees)"),
    )

    additional_info_url = models.CharField(
        null=True,
        blank=True,
        help_text=gettext_lazy("Provide an optional link to a resource with additional information on the project"),
    )  # NOTE: manual_url before

    # TODO: Max length is 10000 in manager dashboard.
    # TODO: This should be required.
    # NOTE: Markdown syntax is supported.
    description = models.TextField(
        null=True,
        blank=True,
    )  # NOTE: project_details before

    # NOTE: JPG and PNG should be supported.
    # TODO: We might need to further validation for image.
    image = models.FileField(
        upload_to=UploadHelper.project_image,
    )  # NOTE: project_image before

    # NOTE: The tutorial should align with what we are looking for.
    tutorial: "Tutorial" = models.ForeignKey(  # type: ignore[reportAssignmentType]
        "tutorial.Tutorial",
        null=True,  # NOTE: Validation makes sure active project have tutorial attached
        blank=True,
        on_delete=models.PROTECT,
        related_name="+",
        help_text=gettext_lazy("Tutorial used for this project."),
    )  # NOTE: tutorial_id before

    # TODO: This should be an integer from 3 to 10000
    verification_number = models.PositiveSmallIntegerField(
        help_text=gettext_lazy("How many people do you want to see every tile before you consider it finished?"),
    )

    # TODO: This should be an integer from 10 to 25
    group_size = models.PositiveSmallIntegerField(
        help_text=gettext_lazy(
            "How big should a mapping session be? Group size refers to the number of tasks per mapping session.",
        ),
    )

    # TODO: This should be an integer from 10 to 250
    # TODO: Empty indicates that no limit is set. But, this field is required in manager dashboard.
    max_tasks_per_user = models.PositiveSmallIntegerField(
        help_text=gettext_lazy("How many tasks each user is allowed to work on for this project"),
        null=True,
        blank=True,
    )

    # TODO: Currently this field collects any data not stored by another fields, pulled from firebase.
    # Also, used in SQL queries
    # FIXME: Refactor this
    project_type_specifics = models.JSONField(blank=True)

    # STATUS

    is_draft = models.BooleanField(default=True, help_text=gettext_lazy("Draft project can be modified"))
    is_featured = models.BooleanField(default=False)
    status: ProjectStatusEnum = IntegerChoicesField(  # type: ignore[reportAssignmentType]
        choices_enum=ProjectStatusEnum,
        default=ProjectStatusEnum.INACTIVE,
    )

    # DEPRECATED

    # TODO: It's not always possible to have geometry during project creation.
    geometry_file = models.FileField(upload_to=UploadHelper.project_geometry, null=True, blank=True)

    # CALCULATED FIELDS

    progress = models.PositiveSmallIntegerField(default=0, validators=[validate_percentage])
    required_results = models.IntegerField(default=0)
    result_count = models.IntegerField(default=0)  # NOTE: All project have 0 in production database

    @typing.override
    def __str__(self):
        return self.name

    def update_status(self, status: ProjectStatusEnum, commit=True):
        self.status = status
        if commit:
            self.save(update_fields=("status",))

    @typing.override
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

    @typing.override
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

    @typing.override
    def __str__(self):
        return f"task_group_id={self.task_group_id}, id={self.pk}"

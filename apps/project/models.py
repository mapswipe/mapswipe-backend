import typing

from django.contrib.gis.db import models as gid_models
from django.db import models
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy
from django_choices_field import IntegerChoicesField

from apps.common.models import UserResource
from utils.fields import PercentageField

if typing.TYPE_CHECKING:
    from apps.tutorial.models import Tutorial


class ProjectType(models.IntegerChoices):
    BUILD_AREA = 1, "Find"
    FOOTPRINT = 2, "Validate"
    CHANGE_DETECTION = 3, "Compare"
    COMPLETENESS = 4, "Completeness"
    MEDIA = 5, "Media"
    DIGITIZATION = 6, "Digitization"
    STREET = 7, "Street"
    # TODO: Confirm if we have more/less


class ProjectStatus(models.IntegerChoices):
    INACTIVE = 1, "Inactive"
    ACTIVE = 2, "Active"
    PRIVATE_FINISHED = 3, "Private finished"
    ARCHIVED = 4, "Archived"
    FINISHED = 5, "Finished"
    # TODO: Paused?


class UploadHelper:
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


class Project(UserResource):
    Type = ProjectType
    Status = ProjectStatus

    name = models.CharField(max_length=255)
    old_project_id = models.CharField(max_length=30, db_index=True, null=True)
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
    project_type = IntegerChoicesField(choices_enum=ProjectType)
    image = models.FileField(upload_to=UploadHelper.project_image)

    # TODO: Currently this field collects any data not stored by another fields, pulled from firebase.
    # Also, used in SQL queries
    # FIXME: Refactor this
    project_type_specifics = models.JSONField()

    is_featured = models.BooleanField(default=False)
    look_for = models.CharField(max_length=255, help_text=gettext_lazy("eg: Buildings and Roads"))
    description = models.TextField(null=True, blank=True)  # NOTE: project_details before
    geometry = gid_models.GeometryField(
        null=True,
        blank=True,
        default=None,
    )  # TODO: < 4 are null in production, change to not nullable?

    progress = PercentageField()
    required_results = models.IntegerField()
    result_count = models.IntegerField()  # NOTE: All project have 0 in production database
    status = IntegerChoicesField(choices_enum=ProjectStatus)  # TODO: default?

    verification_number = models.PositiveSmallIntegerField()  # TODO: More detail required?


class ProjectTaskGroup(models.Model):
    project: Project = models.ForeignKey(  # type: ignore[reportAssignmentType]
        Project,
        on_delete=models.CASCADE,
        related_name="+",
    )

    number_of_tasks = models.IntegerField()
    required_count = models.IntegerField()

    finished_count = models.IntegerField(default=0)
    progress = PercentageField()

    # TODO: Currently this field collects any data not stored by another fields, pulled from firebase.
    # Also, used in SQL queries
    # FIXME: Refactor this
    project_type_specifics = models.JSONField()

    # NOTE: Maintained by Aggregator (Community Dashboard)
    total_area = models.FloatField(null=True, default=None)
    time_spent_max_allowed = models.FloatField(null=True, default=None)

    # Type hints
    project_id: int


class ProjectTask(models.Model):
    task_group: ProjectTaskGroup = models.ForeignKey(  # type: ignore[reportAssignmentType]
        ProjectTaskGroup,
        on_delete=models.CASCADE,
        related_name="+",
    )

    # FIXME: Existing gid_models.MultiPolygonField(srid=4326, blank=True, null=True)
    geometry = gid_models.GeometryField(null=True, blank=True, default=None)

    # TODO: Currently this field collects any data not stored by another fields, pulled from firebase.
    # Also, used in SQL queries
    # FIXME: Refactor this
    project_type_specifics = models.JSONField()

    # Type hints
    task_group_id: int

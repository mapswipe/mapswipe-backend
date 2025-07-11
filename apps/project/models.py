# pyright: reportUninitializedInstanceVariable=false
import typing

import ulid
from django.contrib.gis.db import models as gis_models
from django.db import models
from django.db.models import ExpressionWrapper, Q
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy
from django_choices_field import IntegerChoicesField

from apps.common.models import ArchivableResource, UserResource
from apps.contributor.models import ContributorTeam
from utils.fields import validate_percentage

if typing.TYPE_CHECKING:
    from apps.tutorial.models import Tutorial


class ProjectAssetMimetypeEnum(models.IntegerChoices):
    GEOJSON = 100, "application/geo+json"

    IMAGE_JPEG = 201, "image/jpeg"
    IMAGE_PNG = 202, "image/png"
    IMAGE_GIF = 203, "image/gif"

    @classmethod
    def get_display(cls, value: typing.Self | int) -> str:
        if value in cls:
            return cls(value).label
        return "Unknown"


# FIXME(tnagorra): Finalize the enum labels
class ProjectAssetTypeEnum(models.IntegerChoices):
    INPUT = 100, "Input"
    OUTPUT = 200, "Output"
    STATS = 300, "Stats"

    @classmethod
    def get_display(cls, value: typing.Self | int) -> str:
        if value in cls:
            return cls(value).label
        return "Unknown"


class ProjectTypeEnum(models.IntegerChoices):
    FIND = 1, "Find"
    """ Find project type. Previously known as Classification / Build Area. """

    VALIDATE = 2, "Validate"
    """ Validate project type. Previously known as Footprint """

    COMPARE = 3, "Compare"
    """ Compare project type. Previously known as Change Detection. """

    COMPLETENESS = 4, "Completeness"
    """ Completeness project type. """

    # MEDIA = 5, "Media"
    # DIGITIZATION = 6, "Digitization"
    # STREET = 7, "Street"
    # TODO(thenav56): Confirm if we have more/less

    @classmethod
    def get_display(cls, value: typing.Self | int) -> str:
        if value in cls:
            return cls(value).label
        return "Unknown"


class ProjectStatusEnum(models.IntegerChoices):
    DRAFT = 10, "Draft"
    """
    Background processes and validations will not be triggered for a "Draft" project.
    """

    MARKED_AS_READY = 20, "Marked as Ready"
    """
    Background processes and validations will be triggered
    once a project is "Marked as Ready".
    """

    FAILED = 30, "Failed"
    """
    If there are validation errors or issues with background processes,
    then creation of project has "Failed"
    """

    READY = 40, "Ready"
    """
    If there are no validation errors or issues with background processes,
    then the project is "Ready"
    These projects are not be yet visible to the contributors.
    """

    PUBLISHED = 50, "Published"
    """
    "Published" projects is be visible to the contributors.
    """

    PAUSED = 60, "Paused"
    """
    "Paused" projects are visible to the contributors.
    "Paused" projects can be "un-paused".
    """

    ARCHIVED = 70, "Archived"
    """
    "Archived" projects are not visible to the contributors.
    "Archived" projects cannot be "un-archived".
    """

    DISCARDED = 80, "Discarded"
    """
    "Discarded" projects are not visible to the contributors.
    "Discarded" projects cannot be "un-discarded".
    """


class ProjectProcessingStatusEnum(models.IntegerChoices):
    PREPARING = 10, "Preparing"
    VALIDATING_GEOMETRY = 20, "Validating Geometry"
    GENERATING_GROUPS_AND_TASKS = 30, "Generating groups and tasks"
    ANALYZING_GROUPS_AND_TASK = 40, "Analyzing groups and tasks"
    GENERATING_TASKS_GEOJSON = 50, "Generating GeoJSON from tasks"
    COMPLETED = 60, "Processing Completed"


class UploadHelper:
    @staticmethod
    def project_asset(instance: "ProjectAsset", filename: str):
        return f"project/{instance.project_id}/asset/{instance.type}/{ulid.ULID()!s}/{filename}"

    @staticmethod
    # FIXME: This is not be used anymore
    def project_image(instance: "Project", filename: str):
        return f"project/{instance.pk}/image/{filename}"


class Organization(UserResource, ArchivableResource):  # type: ignore[reportIncompatibleVariableOverride]
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    # TODO: Add icon?

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
    ProcessingStatus = ProjectProcessingStatusEnum

    old_id = models.CharField(max_length=30, db_index=True, null=True, blank=True)

    project_type: int = IntegerChoicesField(  # type: ignore[reportAssignmentType]
        choices_enum=ProjectTypeEnum,
    )

    requesting_organization: Organization = models.ForeignKey(  # type: ignore[reportAssignmentType]
        Organization,
        on_delete=models.PROTECT,
        related_name="+",
        help_text=gettext_lazy("Which group, institution or community is requesting this project?"),
    )

    # TODO(tnagorra): Do we also store project topic, region and number?
    # TODO(tnagorra): Do we add uniqueness on project topic?

    # Generate in manager dashboard based on topic, region, project number, requesting org
    name = models.CharField(max_length=255)

    # TODO(tnagorra): Max length is 25 in manager dashboard.
    # TODO(frozenhelium): We should discuss if we need this field.
    look_for = models.CharField(
        max_length=255,
        help_text=gettext_lazy("What should the users look for (e.g. buildings, cars, trees)"),
    )

    additional_info_url = models.CharField(
        null=True,
        blank=True,
        help_text=gettext_lazy("Provide an optional link to a resource with additional information on the project"),
    )  # NOTE: manual_url before

    # TODO(tnagorra): Max length is 10000 in manager dashboard.
    # TODO(tnagorra): This should be required.
    # NOTE: Markdown syntax is supported.
    description = models.TextField(
        null=True,
        blank=True,
    )  # NOTE: project_details before

    # NOTE: JPG and PNG should be supported.
    image: "ProjectAsset | None" = models.ForeignKey(  # type: ignore[reportAssignmentType]
        "project.ProjectAsset",
        related_name="+",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    # FIXME(tnagorra): We might need to rename this field
    # NOTE: The tutorial should align with what we are looking for.
    tutorial: "Tutorial" = models.ForeignKey(  # type: ignore[reportAssignmentType]
        "tutorial.Tutorial",
        null=True,  # NOTE: Validation makes sure active project have tutorial attached
        blank=True,
        on_delete=models.PROTECT,
        related_name="+",
        help_text=gettext_lazy("Tutorial used for this project."),
    )  # NOTE: tutorial_id before

    # TODO(tnagorra): This should be an integer from 3 to 10000
    verification_number = models.PositiveSmallIntegerField(
        help_text=gettext_lazy("How many people do you want to see every tile before you consider it finished?"),
        default=3,
    )

    # TODO(tnagorra): This should be an integer from 10 to 25
    group_size = models.PositiveSmallIntegerField(
        help_text=gettext_lazy(
            "How big should a mapping session be? Group size refers to the number of tasks per mapping session.",
        ),
        default=10,
    )

    # TODO(tnagorra): This should be an integer from 10 to 250
    # TODO(tnagorra): Empty indicates that no limit is set. But, this field is required in manager dashboard.
    max_tasks_per_user = models.PositiveSmallIntegerField(
        help_text=gettext_lazy("How many tasks each user is allowed to work on for this project"),
        null=True,
        blank=True,
        default=10,
    )

    # TODO(tnagorra): Currently this field collects any data not stored by another fields, pulled from firebase.
    # Also, used in SQL queries
    project_type_specifics = models.JSONField(blank=True, null=True)

    project_type_specific_output: "ProjectAsset | None" = models.ForeignKey(  # type: ignore[reportAssignmentType]
        "project.ProjectAsset",
        related_name="+",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    # TODO(thenav56): Use srid=4326?
    centroid = gis_models.PointField(blank=True, null=True)

    # STATUS

    is_featured = models.BooleanField(default=False)
    status: int = IntegerChoicesField(  # type: ignore[reportAssignmentType]
        choices_enum=ProjectStatusEnum,
        default=ProjectStatusEnum.DRAFT,
    )
    processing_status: int = IntegerChoicesField(  # type: ignore[reportAssignmentType]
        choices_enum=ProjectProcessingStatusEnum,
        null=True,
        blank=True,
    )

    # TEAM

    # NOTE: If any team is attached to the project, then project should only visible to the team members.
    team: ContributorTeam | None = models.OneToOneField(  # type: ignore[reportAssignmentType]
        ContributorTeam,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    is_private = models.GeneratedField(
        expression=ExpressionWrapper(
            Q(team__isnull=False),
            output_field=models.BooleanField(),
        ),
        output_field=models.BooleanField(),
        db_persist=True,
        help_text=gettext_lazy(
            "If the project is private, then it is only visible to the team members.",
        ),
    )

    # CALCULATED FIELDS

    progress = models.PositiveSmallIntegerField(default=0, validators=[validate_percentage])
    required_results = models.IntegerField(default=0)
    result_count = models.IntegerField(default=0)  # NOTE: All project have 0 in production database

    # Type hints
    requesting_organization_id: int
    tutorial_id: int | None
    image_id: int | None
    team_id: int | None
    project_type_specific_output_id: int | None

    @typing.override
    def __str__(self):
        return self.name

    @property
    def project_type_enum(self):
        return ProjectTypeEnum(self.project_type)

    def update_status(self, status: ProjectStatusEnum, commit: bool = True):
        self.status = status
        if commit:
            self.save(update_fields=("status",))

    def update_processing_status(self, status: ProjectProcessingStatusEnum, commit: bool = True):
        self.processing_status = status
        if commit:
            self.save(update_fields=("processing_status",))

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


class ProjectAsset(UserResource):
    Type = ProjectAssetTypeEnum
    Mimetype = ProjectAssetMimetypeEnum

    type = IntegerChoicesField(
        choices_enum=ProjectAssetTypeEnum,
    )

    mimetype = IntegerChoicesField(
        choices_enum=ProjectAssetMimetypeEnum,
    )

    file = models.FileField(
        upload_to=UploadHelper.project_asset,
        help_text=gettext_lazy("The file associated with the asset"),
    )

    project: Project = models.ForeignKey(  # type: ignore[reportAssignmentType]
        Project,
        on_delete=models.CASCADE,
        related_name="+",
    )

    marked_as_deleted = models.BooleanField(
        default=False,
        help_text=gettext_lazy("If this flag is enabled, this project asset will be deleted in the future"),
    )

    @classmethod
    def usable_objects(cls):
        """Returns objects that are mot marked for deletion"""
        return cls.objects.filter(marked_as_deleted=False)

    # Type hints
    project_id: int


class ProjectTaskGroup(models.Model):
    # FIXME(tnagorra): We might need to skip the indexing
    old_id = models.CharField(max_length=30, db_index=True, null=True)

    project: Project = models.ForeignKey(  # type: ignore[reportAssignmentType]
        Project,
        on_delete=models.CASCADE,
        related_name="+",
    )

    number_of_tasks = models.IntegerField()
    required_count = models.IntegerField()

    finished_count = models.IntegerField(default=0)
    progress = models.PositiveSmallIntegerField(default=0, validators=[validate_percentage])

    # TODO(thenav56): Currently this field collects any data not stored by another fields, pulled from firebase.
    # Also, used in SQL queries
    # FIXME(thenav56): Refactor this
    project_type_specifics = models.JSONField()

    # NOTE: Used by Community Dashboard
    total_area = models.FloatField(null=True, default=None)
    time_spent_max_allowed = models.FloatField(null=True, default=None)

    # Type hints
    project_id: int

    @typing.override
    def __str__(self):
        return f"(project={self.project_id}, id={self.pk})"


class ProjectTask(models.Model):
    # FIXME(tnagorra): We might need to skip the indexing
    old_id = models.CharField(max_length=30, db_index=True, null=True)

    task_group: ProjectTaskGroup = models.ForeignKey(  # type: ignore[reportAssignmentType]
        ProjectTaskGroup,
        on_delete=models.CASCADE,
        related_name="+",
    )

    # NOTE(tnagorra): The geometry is only necessary for validate project type
    # FIXME(thenav56): Existing gid_models.MultiPolygonField(srid=4326, blank=True, null=True)
    geometry = gis_models.GeometryField(null=True, blank=True, default=None, dim=2)

    # TODO(thenav56): Currently this field collects any data not stored by another fields, pulled from firebase.
    # Also, used in SQL queries
    # FIXME(thenav56): Refactor this
    project_type_specifics = models.JSONField()

    # Type hints
    task_group_id: int

    @typing.override
    def __str__(self):
        return f"task_group_id={self.task_group_id}, id={self.pk}"

# pyright: reportUninitializedInstanceVariable=false
import typing
from warnings import deprecated

from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import GEOSGeometry
from django.db import models
from django.db.models import ExpressionWrapper, Q
from django.db.models.expressions import Value
from django.db.models.functions import Concat, Lower
from django.utils.translation import gettext_lazy
from django_choices_field import IntegerChoicesField
from pyfirebase_mapswipe import models as firebase_models

from apps.common.models import (
    ArchivableResource,
    AssetMimetypeEnum,
    AssetTypeEnum,
    CommonAsset,
    FirebasePushResource,
    UserResource,
)
from apps.contributor.models import ContributorTeam
from main.fields import OverwritableFileField
from utils.fields import validate_percentage

if typing.TYPE_CHECKING:
    from apps.tutorial.models import Tutorial  # noqa: F401


class ProjectAssetInputTypeEnum(models.IntegerChoices):
    AOI_GEOMETRY = 100, "AOI Geometry"
    OBJECT_IMAGE = 200, "Image with object annotations"
    COVER_IMAGE = 201, "Image for project cover"

    @classmethod
    def get_display(cls, value: typing.Self | int) -> str:
        if value in cls:
            return str(cls(value).label)
        return "Unknown"


class ProjectAssetExportTypeEnum(models.IntegerChoices):
    # Common?
    AGGREGATED_RESULTS = 100, "Aggregated Results (CSV)"
    AGGREGATED_RESULTS_WITH_GEOMETRY = 101, "Aggregated Results (with Geometry) (GEOJSON)"
    GROUPS = 104, "Groups (CSV)"
    HISTORY = 105, "History (CSV)"
    RESULTS = 106, "Results (CSV)"
    TASKS = 107, "Tasks (CSV)"
    USERS = 108, "Users (CSV)"
    AREA_OF_INTEREST = 109, "Area of Interest (GEOJSON)"
    # FIND / COMPARE
    HOT_TASKING_MANAGER_GEOMETRIES = 200, "HOT Tasking Manager Geometries (GEOJSON)"
    MODERATE_TO_HIGH_AGREEMENT_YES_MAYBE_GEOMETRIES = 201, "Moderate to High Agreement Yes Maybe Geometries (GEOJSON)"

    @classmethod
    def get_display(cls, value: typing.Self | int) -> str:
        if value in cls:
            return str(cls(value).label)
        return "Unknown"

    @staticmethod
    def get_mimetype(export_type: "ProjectAssetExportTypeEnum"):
        if export_type == ProjectAssetExportTypeEnum.AGGREGATED_RESULTS:
            return AssetMimetypeEnum.GZIP
        if export_type == ProjectAssetExportTypeEnum.AGGREGATED_RESULTS_WITH_GEOMETRY:
            return AssetMimetypeEnum.GZIP
        if export_type == ProjectAssetExportTypeEnum.GROUPS:
            return AssetMimetypeEnum.GZIP
        if export_type == ProjectAssetExportTypeEnum.HISTORY:
            return AssetMimetypeEnum.CSV
        if export_type == ProjectAssetExportTypeEnum.RESULTS:
            return AssetMimetypeEnum.GZIP
        if export_type == ProjectAssetExportTypeEnum.TASKS:
            return AssetMimetypeEnum.GZIP
        if export_type == ProjectAssetExportTypeEnum.USERS:
            return AssetMimetypeEnum.GZIP
        if export_type == ProjectAssetExportTypeEnum.AREA_OF_INTEREST:
            return AssetMimetypeEnum.GEOJSON
        if export_type == ProjectAssetExportTypeEnum.MODERATE_TO_HIGH_AGREEMENT_YES_MAYBE_GEOMETRIES:
            return AssetMimetypeEnum.GEOJSON
        if export_type == ProjectAssetExportTypeEnum.HOT_TASKING_MANAGER_GEOMETRIES:
            return AssetMimetypeEnum.GEOJSON
        typing.assert_never(export_type)


class ProjectTypeEnum(models.IntegerChoices):
    FIND = 1, "Find"
    """ Find project type. Previously known as Classification / Build Area. """

    VALIDATE = 2, "Validate"
    """ Validate project type. Previously known as Footprint """

    VALIDATE_IMAGE = 10, "Validate Image"
    """ Validate image project type. """

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
            return str(cls(value).label)
        return "Unknown"

    def to_firebase(self) -> firebase_models.FbEnumProjectType:
        match self:
            case ProjectTypeEnum.FIND:
                return firebase_models.FbEnumProjectType.FIND
            case ProjectTypeEnum.COMPARE:
                return firebase_models.FbEnumProjectType.COMPARE
            case ProjectTypeEnum.COMPLETENESS:
                return firebase_models.FbEnumProjectType.COMPLETENESS
            case ProjectTypeEnum.VALIDATE:
                return firebase_models.FbEnumProjectType.VALIDATE
            case ProjectTypeEnum.VALIDATE_IMAGE:
                return firebase_models.FbEnumProjectType.VALIDATE_IMAGE


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
        client_id = instance.client_id
        asset_type_str = AssetTypeEnum.get_string_for_filepath(instance.type_enum)
        return f"project/{instance.project_id}/asset/{asset_type_str}/{client_id}/{filename}"

    @deprecated("This is kept because it's referenced in migrations")
    @staticmethod
    def project_image(instance: "Project", filename: str):
        return f"project/{instance.pk}/image/{filename}"


class Organization(UserResource, ArchivableResource, FirebasePushResource):  # type: ignore[reportIncompatibleVariableOverride]
    name = models.CharField[str, str](max_length=255)
    description = models.TextField[str | None, str | None](null=True, blank=True)
    abbreviation = models.CharField[str, str](max_length=50, null=True, blank=True)
    # TODO(Rup-Narayan-Rajbanshi): Add icon?

    unique_name = models.GeneratedField(
        expression=Lower("name"),
        output_field=models.CharField(),
        db_persist=True,
        unique=True,
    )

    @typing.override
    def __str__(self) -> str:
        return self.name


class Project(UserResource, FirebasePushResource):
    Type = ProjectTypeEnum
    Status = ProjectStatusEnum
    ProcessingStatus = ProjectProcessingStatusEnum

    project_type: int = IntegerChoicesField(  # type: ignore[reportAssignmentType]
        choices_enum=ProjectTypeEnum,
    )

    requesting_organization = models.ForeignKey[Organization, Organization](
        Organization,
        on_delete=models.PROTECT,
        related_name="+",
        help_text=gettext_lazy("Which group, institution or community is requesting this project?"),
    )

    # TODO(tnagorra): Do we also store project topic, region and number?
    # TODO(tnagorra): Do we add uniqueness on project topic?

    # Generate in manager dashboard based on topic, region, project number, requesting org
    topic = models.CharField[str, str](max_length=255)
    region = models.CharField[str, str](max_length=255)
    project_number = models.PositiveIntegerField[int, int]()

    # TODO(tnagorra): Max length is 25 in manager dashboard.
    # TODO(frozenhelium): We should discuss if we need this field.
    look_for = models.CharField[str | None, str | None](
        null=True,
        blank=True,
        max_length=255,
        help_text=gettext_lazy("What should the users look for (e.g. buildings, cars, trees)"),
    )

    additional_info_url = models.CharField[str | None, str | None](
        null=True,
        blank=True,
        help_text=gettext_lazy("Provide an optional link to a resource with additional information on the project"),
    )  # NOTE: manual_url before

    # TODO(tnagorra): Max length is 10000 in manager dashboard.
    # TODO(tnagorra): This should be required.
    # NOTE: Markdown syntax is supported.
    description = models.TextField[str | None, str | None](
        null=True,
        blank=True,
    )  # NOTE: project_details before

    project_instruction = models.TextField[str | None, str | None](
        null=True,
        blank=True,
        help_text=gettext_lazy(
            "Provide project instruction",
        ),
    )

    # NOTE: JPG and PNG should be supported.
    image = models.ForeignKey["ProjectAsset | None", "ProjectAsset | None"](
        "project.ProjectAsset",
        related_name="+",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    # FIXME(tnagorra): We might need to rename this field
    # NOTE: The tutorial should align with what we are looking for.
    tutorial = models.ForeignKey["Tutorial | None", "Tutorial | None"](
        "tutorial.Tutorial",
        null=True,  # NOTE: Validation makes sure active project have tutorial attached
        blank=True,
        on_delete=models.PROTECT,
        related_name="+",
        help_text=gettext_lazy("Tutorial used for this project."),
    )  # NOTE: tutorial_id before

    # TODO(tnagorra): This should be an integer from 3 to 10000
    verification_number = models.PositiveSmallIntegerField[int, int](
        help_text=gettext_lazy("How many people do you want to see every tile before you consider it finished?"),
        default=3,
    )

    # TODO(tnagorra): This should be an integer from 10 to 25
    group_size = models.PositiveSmallIntegerField[int, int](
        help_text=gettext_lazy(
            "How big should a mapping session be? Group size refers to the number of tasks per mapping session.",
        ),
        default=10,
    )

    # TODO(tnagorra): This should be an integer from 10 to 250
    # TODO(tnagorra): Empty indicates that no limit is set. But, this field is required in manager dashboard.
    max_tasks_per_user = models.PositiveSmallIntegerField[int, int](
        help_text=gettext_lazy("How many tasks each user is allowed to work on for this project"),
        null=True,
        blank=True,
        default=10,
    )

    # TODO(tnagorra): Currently this field collects any data not stored by another fields, pulled from firebase.
    # Also, used in SQL queries
    project_type_specifics = models.JSONField(blank=True, null=True)

    # FIXME(tnagorra): Do we need to reference this to project table?
    project_type_specific_output = models.ForeignKey["ProjectAsset | None", "ProjectAsset | None"](
        "project.ProjectAsset",
        related_name="+",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    # TODO(thenav56): Use srid=4326?
    centroid = gis_models.PointField(blank=True, null=True)

    # STATUS

    is_featured = models.BooleanField[bool, bool](default=False)
    status: int = IntegerChoicesField(  # type: ignore[reportAssignmentType]
        choices_enum=ProjectStatusEnum,
        default=ProjectStatusEnum.DRAFT,
    )
    processing_status: int | None = IntegerChoicesField(  # type: ignore[reportAssignmentType]
        choices_enum=ProjectProcessingStatusEnum,
        null=True,
        blank=True,
    )

    # TEAM

    # NOTE: If any team is attached to the project, then project should only visible to the team members.
    team = models.OneToOneField[ContributorTeam | None, ContributorTeam | None](
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

    progress = models.PositiveSmallIntegerField[int, int](default=0, validators=[validate_percentage])
    required_results = models.IntegerField[int, int](default=0)
    result_count = models.IntegerField[int, int](default=0)  # NOTE: All project have 0 in production database

    # Type hints
    requesting_organization_id: int
    tutorial_id: int | None
    image_id: int | None
    team_id: int | None
    project_type_specific_output_id: int | None

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        constraints = [
            models.UniqueConstraint(
                Lower("topic"),
                Lower("region"),
                "project_number",
                "requesting_organization",
                name="unique_project_name",
                violation_error_message=gettext_lazy(
                    "A project with the same topic, region, project number and requesting organization already exists.",
                ),
            ),
        ]

    @typing.override
    def __str__(self) -> str:
        return self.generate_name()

    def generate_name(self) -> str:
        """
        Returns a generated name for the project based on topic, region and project number.

        Use select_related to avoid N+1 queries.
        """
        # Format: "{topic} - {region} ({project_number}) {requesting_organization.name}"
        return f"{self.topic} - {self.region} ({self.project_number}) {self.requesting_organization.name}"

    @staticmethod
    def generate_name_query(prefix: str = ""):
        """
        Returns a Django QuerySet expression to generate the project name.
        """
        return Concat(
            models.F(f"{prefix}topic"),
            Value(" - "),
            models.F(f"{prefix}region"),
            Value(" ("),
            models.F(f"{prefix}project_number"),
            Value(") "),
            models.F(f"{prefix}requesting_organization__name"),
            output_field=models.CharField(),
        )

    def update_status(self, status: ProjectStatusEnum, commit: bool = True):
        self.status = status
        if commit:
            self.save(update_fields=("status",))

    def update_processing_status(self, status: ProjectProcessingStatusEnum, commit: bool = True):
        self.processing_status = status
        if commit:
            self.save(update_fields=("processing_status",))

    @property
    def project_type_enum(self):
        return ProjectTypeEnum(self.project_type)

    @property
    def status_enum(self):
        return ProjectStatusEnum(self.status)

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


class ProjectAsset(UserResource, CommonAsset):  # type: ignore[reportIncompatibleVariableOverride]
    # TODO(thenav56): add validation
    # Type specific nested types
    export_type: int | None = IntegerChoicesField(  # type: ignore[reportAssignmentType]
        choices_enum=ProjectAssetExportTypeEnum,
        blank=True,
        null=True,
    )
    input_type: int | None = IntegerChoicesField(  # type: ignore[reportAssignmentType]
        choices_enum=ProjectAssetInputTypeEnum,
        blank=True,
        null=True,
    )

    project = models.ForeignKey[Project, Project](
        Project,
        on_delete=models.CASCADE,
        related_name="+",
    )

    file = OverwritableFileField(
        upload_to=UploadHelper.project_asset,
        help_text=gettext_lazy("The file associated with the asset"),
        null=True,
        blank=True,
    )

    # This depends on the input_type
    asset_type_specifics = models.JSONField(default=dict)

    @property
    def input_type_enum(self):
        return ProjectAssetInputTypeEnum(self.input_type)

    # Type hints
    project_id: int


class ProjectTaskGroup(FirebasePushResource):
    firebase_id = models.CharField[str, str](max_length=30)

    project: Project = models.ForeignKey[Project, Project](  # type: ignore[reportAssignmentType]
        Project,
        on_delete=models.CASCADE,
        related_name="+",
    )

    number_of_tasks = models.IntegerField[int, int]()
    required_count = models.IntegerField[int, int]()

    finished_count = models.IntegerField[int, int](default=0)
    progress = models.PositiveSmallIntegerField[int, int](default=0, validators=[validate_percentage])

    # TODO(thenav56): Currently this field collects any data not stored by another fields, pulled from firebase.
    # Also, used in SQL queries
    # FIXME(thenav56): Refactor this
    project_type_specifics = models.JSONField()

    # NOTE: Used by Community Dashboard
    total_area = models.FloatField[float | None, float | None](null=True, default=None)
    time_spent_max_allowed = models.FloatField[float | None, float | None](null=True, default=None)

    # Type hints
    id: int
    project_id: int

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        unique_together = (
            "project",
            "firebase_id",
        )

    @typing.override
    def __str__(self):
        return f"(project={self.project_id}, id={self.pk})"


class ProjectTask(FirebasePushResource):
    firebase_id = models.CharField[str, str](max_length=30)

    task_group: ProjectTaskGroup = models.ForeignKey[ProjectTaskGroup, ProjectTaskGroup](  # type: ignore[reportAssignmentType]
        ProjectTaskGroup,
        on_delete=models.CASCADE,
        related_name="+",
    )

    # NOTE(tnagorra): The geometry is only necessary for validate project type
    # FIXME(thenav56): Existing gid_models.MultiPolygonField(srid=4326, blank=True, null=True)
    geometry: GEOSGeometry | None = gis_models.GeometryField(null=True, blank=True, default=None, dim=2)  # type: ignore[reportIncompatibleVariableOverride]

    # TODO(thenav56): Currently this field collects any data not stored by another fields, pulled from firebase.
    # Also, used in SQL queries
    # FIXME(thenav56): Refactor this
    project_type_specifics = models.JSONField()

    # Type hints
    id: int
    task_group_id: int

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        unique_together = (
            # FIXME(tnagorra): Should we use project instead of task_group here?
            "task_group",
            "firebase_id",
        )

    @typing.override
    def __str__(self):
        return f"task_group_id={self.task_group_id}, id={self.pk}"

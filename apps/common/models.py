# pyright: reportUninitializedInstanceVariable=false
import datetime
import typing

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy
from django_choices_field import IntegerChoicesField
from django_stubs_ext.db.models import TypedModelMeta
from django_stubs_ext.db.models.manager import RelatedManager
from ulid import ULID

from main.db import Model
from main.fields import OverwritableFileField
from utils.common import validate_ulid

if typing.TYPE_CHECKING:
    from apps.user.models import User  # noqa: F401, RUF100, TC004


class FirebasePushStatusEnum(models.IntegerChoices):
    """Enum representing the status of a data push operation to firebase."""

    PENDING = 1, "Pending"
    PROCESSING = 2, "Processing"
    SUCCESS = 3, "Success"
    FAILED = 4, "Failed"


class UploadHelper:
    """Utility class providing helper functions for generating upload paths."""

    @staticmethod
    def common_asset(instance: "CommonAsset", filename: str):
        return f"common/asset/{instance.type}/{ULID()!s}/{filename}"


# -- Abstracts
class UserResource(Model):
    """Abstract base model for resources created or modified by a user."""

    client_id = models.CharField[str, str](
        null=False,
        blank=False,
        unique=True,
        max_length=26,
        validators=[validate_ulid],
    )
    created_at = models.DateTimeField[datetime.datetime, datetime.datetime](auto_now_add=True)
    modified_at = models.DateTimeField[datetime.datetime, datetime.datetime](auto_now=True)
    created_by = models.ForeignKey["User", "User"](
        "user.User",
        related_name="%(class)s_created",
        on_delete=models.PROTECT,
    )
    modified_by = models.ForeignKey["User", "User"](
        "user.User",
        related_name="%(class)s_modified",
        on_delete=models.PROTECT,
    )

    # Typing
    id: int
    created_by_id: int
    modified_by_id: int

    class Meta(TypedModelMeta):  # type: ignore[reportIncompatibleVariableOverride]
        abstract = True
        ordering = ["-id"]

    @typing.override
    def __str__(self):
        return str(self.pk)


class ArchivableResource(Model):
    """Abstract base model that adds archiving capability to resources."""

    is_archived = models.BooleanField[bool, bool](default=False)
    archived_at = models.DateTimeField[datetime.datetime | None, datetime.datetime | None](null=True, blank=True)
    archived_by = models.ForeignKey["User", "User"](
        "user.User",
        related_name="+",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    # Type hints
    archived_by_id: int | None

    class Meta(TypedModelMeta):  # type: ignore[reportIncompatibleVariableOverride]
        abstract = True
        ordering = ["-id"]


# NOTE: The labels should not be edited.
# If the change is absolutely required, it requires migrating data in firebase as well.
class IconEnum(models.IntegerChoices):
    """Enum representing the icons available for use in custom options and tutorial instructions."""

    ADD_OUTLINE = 1, "add-outline"
    ALERT_OUTLINE = 2, "alert-outline"
    BAN_OUTLINE = 3, "ban-outline"
    CHECK = 4, "check"
    CLOSE_OUTLINE = 5, "close-outline"
    CHECKMARK_OUTLINE = 33, "checkmark-outline"
    EGG_OUTLINE = 6, "egg-outline"
    ELLIPSE_OUTLINE = 7, "ellipse-outline"
    FLAG_OUTLINE = 8, "flag-outline"
    HAND_LEFT_OUTLINE = 9, "hand-left-outline"
    HAND_RIGHT_OUTLINE = 10, "hand-right-outline"
    HAPPY_OUTLINE = 11, "happy-outline"
    HEART_OUTLINE = 12, "heart-outline"
    HELP_OUTLINE = 13, "help-outline"
    INFORMATION_OUTLINE = 14, "information-outline"
    PRISM_OUTLINE = 15, "prism-outline"
    REFRESH_OUTLINE = 16, "refresh-outline"
    REMOVE_OUTLINE = 17, "remove-outline"
    SAD_OUTLINE = 18, "sad-outline"
    SEARCH_OUTLINE = 19, "search-outline"
    SHAPES_OUTLINE = 20, "shapes-outline"
    SQUARE_OUTLINE = 21, "square-outline"
    STAR_OUTLINE = 22, "star-outline"
    THUMBS_DOWN_OUTLINE = 23, "thumbs-down-outline"
    THUMBS_UP_OUTLINE = 24, "thumbs-up-outline"
    TRIANGLE_OUTLINE = 25, "triangle-outline"
    WARNING_OUTLINE = 26, "warning-outline"
    GENERAL_TAP = 27, "general-tap"
    TAP = 28, "tap"
    TAP_1 = 29, "tap-1"
    TAP_2 = 30, "tap-2"
    TAP_3 = 31, "tap-3"
    SWIPE_LEFT = 32, "swipe-left"


class FirebasePushResource(Model):
    """Abstract base model to track firebase data push operation for resources."""

    # NOTE: We should not directly use old_id. This is ID reference to old system
    old_id = models.CharField[str | None, str | None](max_length=30, db_index=True, null=True, blank=True)

    # NOTE: Panoramax uses UUIDv4 (length 36) for identifiers, which we use as firebase_id for street project tasks
    firebase_id = models.CharField[str, str](max_length=36, unique=True, default=ULID)

    firebase_push_status: int | None = IntegerChoicesField(  # type: ignore[reportAssignmentType]
        choices_enum=FirebasePushStatusEnum,
        null=True,
        blank=True,
    )
    firebase_last_pushed = models.DateTimeField[datetime.datetime | None, datetime.datetime | None](
        null=True,
        blank=True,
        help_text=gettext_lazy("The latest time when resource was pushed to firebase"),
    )

    @property
    def firebase_push_status_enum(self):
        if self.firebase_push_status:
            return FirebasePushStatusEnum(self.firebase_push_status)
        return None

    def update_firebase_push_status(
        self,
        firebase_push_status: FirebasePushStatusEnum,
        commit: bool = True,
    ):
        self.firebase_push_status = firebase_push_status
        update_fields = ["firebase_push_status"]

        if firebase_push_status == FirebasePushStatusEnum.SUCCESS:
            self.firebase_last_pushed = timezone.now()
            update_fields.append("firebase_last_pushed")

        if commit:
            self.save(update_fields=update_fields)

    class Meta(TypedModelMeta):  # type: ignore[reportIncompatibleVariableOverride]
        abstract = True


class FirebasePullResource(Model):
    """Abstract base model to track firebase data pull operation for resources."""

    firebase_id = models.CharField[str, str](max_length=30, unique=True)

    firebase_last_pulled = models.DateTimeField[datetime.datetime | None, datetime.datetime | None](
        null=True,
        blank=True,
        help_text=gettext_lazy("The latest time when resource was pulled from firebase"),
    )

    class Meta(TypedModelMeta):  # type: ignore[reportIncompatibleVariableOverride]
        abstract = True


class AssetMimetypeEnum(models.IntegerChoices):
    """Enum representing the supported MIME types for assets."""

    GEOJSON = 100, "application/geo+json"
    JSON = 101, "application/json"

    IMAGE_JPEG = 201, "image/jpeg"
    IMAGE_PNG = 202, "image/png"
    IMAGE_GIF = 203, "image/gif"

    GZIP = 300, "application/x-gzip"

    CSV = 400, "text/csv"

    PLAINTEXT = 500, "text/plain"

    @classmethod
    def get_display(cls, value: typing.Self | int) -> str:
        if value in cls:
            return str(cls(value).label)
        return "Unknown"

    @classmethod
    def is_valid_mimetype(cls, mimetype: str) -> bool:
        """Check if the given mimetype is valid for project assets."""
        return mimetype in [choice.label for choice in cls]

    @classmethod
    def get_mimetype_by_label(cls, label: str) -> typing.Self | None:
        for choice in cls:
            if choice.label == label:
                return choice
        return None


# FIXME(tnagorra): Finalize the enum labels
class AssetTypeEnum(models.IntegerChoices):
    """Enum representing the types of assets."""

    INPUT = 100, "Input"
    OUTPUT = 200, "Output"
    EXPORT = 300, "Export"
    DEBUG = 400, "Debug"

    @classmethod
    def get_display(cls, value: typing.Self | int) -> str:
        if value in cls:
            return str(cls(value).label)
        return "Unknown"

    @classmethod
    def get_string_for_filepath(cls, value: typing.Self) -> str:
        if value == cls.INPUT:
            return "input"
        if value == cls.OUTPUT:
            return "output"
        if value == cls.EXPORT:
            return "export"
        if value == cls.DEBUG:
            return "debug"
        typing.assert_never(value)


class CommonAsset(Model):
    """Abstract model representing a common asset with associated metadata."""

    Mimetype = AssetMimetypeEnum
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # MB
    Type = AssetTypeEnum

    type: int = IntegerChoicesField(  # type: ignore[reportAssignmentType]
        choices_enum=AssetTypeEnum,
    )

    mimetype: int | None = IntegerChoicesField(  # type: ignore[reportAssignmentType]
        choices_enum=AssetMimetypeEnum,
        null=True,
        blank=True,
    )

    file_size = models.PositiveIntegerField[int, int](
        help_text=gettext_lazy("The size of the file in bytes"),
    )

    marked_as_deleted = models.BooleanField[bool, bool](
        default=False,
        help_text=gettext_lazy("If this flag is enabled, this asset will be deleted in the future"),
    )

    # TODO: Use OverwritableFileField?
    file = models.FileField(
        upload_to=UploadHelper.common_asset,
        help_text=gettext_lazy("The file associated with the asset"),
        null=True,
        blank=True,
        max_length=255,
    )

    external_url = models.CharField[str | None, str | None](
        null=True,
        blank=True,
        help_text=gettext_lazy("Provide link to the file associated with the asset"),
    )

    class Meta(TypedModelMeta):  # type: ignore[reportIncompatibleVariableOverride]
        abstract = True

    @property
    def type_enum(self):
        return AssetTypeEnum(self.type)

    @classmethod
    def usable_objects(cls):
        """Get objects that are mot marked for deletion."""
        return cls.objects.filter(marked_as_deleted=False)


# Models


class GlobalExportAssetTypeEnum(models.IntegerChoices):
    """Enum representing the types of global export assets."""

    PROJECT_STATS_BY_TYPES = 1, "Project Type Aggregates"
    """Previously known as /api/stats.csv."""

    PROJECTS_CSV = 2, "All projects"
    """Previously known as /api/projects/projects.csv."""

    PROJECTS_CENTROID_GEOJSON = 3, "Projects geojson with centroid"
    """Previously known as /api/projects/projects_centroid.geojson."""

    PROJECTS_GEOM_GEOJSON = 4, "Projects Geojson with GEOM"
    """Previously known as /api/projects/projects_geom.geojson."""

    @classmethod
    def get_file_name(cls, enum_value: typing.Self):
        if enum_value == cls.PROJECT_STATS_BY_TYPES:
            return "project_stats_by_types.csv"
        if enum_value == cls.PROJECTS_CSV:
            return "projects.csv"
        if enum_value == cls.PROJECTS_CENTROID_GEOJSON:
            return "projects_centroid.geojson"
        if enum_value == cls.PROJECTS_GEOM_GEOJSON:
            return "projects_geom.geojson"
        typing.assert_never(enum_value)


class GlobalExportAsset(models.Model):
    """Model representing a global export asset with associated metadata."""

    type: int = IntegerChoicesField(  # type: ignore[reportAssignmentType]
        choices_enum=GlobalExportAssetTypeEnum,
        primary_key=True,
    )

    file_size = models.PositiveIntegerField[int, int](
        help_text=gettext_lazy("The size of the file in bytes"),
    )

    file = OverwritableFileField(
        upload_to="global/asset/",
        help_text=gettext_lazy("The file associated with the asset"),
        null=True,
        blank=True,
        max_length=255,
    )

    last_updated_at = models.DateTimeField[datetime.datetime, datetime.datetime](auto_now=True)

    @typing.override
    def __str__(self):
        return f"{self.type_enum.label}"

    @property
    def type_enum(self):
        return GlobalExportAssetTypeEnum(self.type)


class Announcement(UserResource, FirebasePushResource):  # type: ignore[reportIncompatibleVariableOverride]
    """Model representing an announcement.

    Only one announcement can be active at a time.
    """

    text = models.TextField[str, str]()
    url = models.URLField[str, str](max_length=300)
    is_active = models.BooleanField[bool, bool](default=False)

    @typing.override
    def __str__(self):
        return self.text


# -- App info (mobile app version check)
APP_VERSION_VALIDATOR = RegexValidator(
    # NOTE: minor and patch are limited to 3 digits to generate the version code
    regex=r"^\d+\.\d{1,3}\.\d{1,3}$",
    message=gettext_lazy("Enter a version like 3.0.10"),
)


def get_app_version_code(version: str) -> int:
    """Return a sortable number for the version. Eg: 3.0.10 -> 3000010."""
    major, minor, patch = (int(part) for part in version.split("."))
    return major * 1_000_000 + minor * 1_000 + patch


class AppPlatformEnum(models.IntegerChoices):
    """Enum representing the mobile app platforms."""

    IOS = 1, "ios"
    ANDROID = 2, "android"


class AppInfo(UserResource, FirebasePushResource):  # type: ignore[reportIncompatibleVariableOverride]
    """Version information of the mobile app for a platform.

    There is one row per platform, created by the migration. It is pushed to firebase at /v2/appInfo/{platform}.
    """

    # NOTE: The rows are created by the migration without a user, so these are optional
    created_by = models.ForeignKey["User | None", "User | None"](
        "user.User",
        related_name="%(class)s_created",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    modified_by = models.ForeignKey["User | None", "User | None"](
        "user.User",
        related_name="%(class)s_modified",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    created_by_id: int | None  # type: ignore[reportIncompatibleVariableOverride]
    modified_by_id: int | None  # type: ignore[reportIncompatibleVariableOverride]

    platform: int = IntegerChoicesField(choices_enum=AppPlatformEnum, unique=True)  # type: ignore[reportAssignmentType]
    latest_version_id: int | None
    latest_version = models.ForeignKey["AppRelease | None", "AppRelease | None"](
        "AppRelease",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=gettext_lazy(
            "Set this once the release is available on the store. Only releases up to this version are published.",
        ),
    )
    min_supported_version = models.CharField[str, str](
        max_length=20,
        default="0.0.0",
        validators=[APP_VERSION_VALIDATOR],
        help_text=gettext_lazy("Installed versions below this are forced to update."),
    )

    releases: RelatedManager["AppRelease"]

    @typing.override
    def __str__(self):
        return str(self.platform_enum.label)

    @typing.override
    def clean(self):
        super().clean()
        latest_version = self.latest_version
        if latest_version is None:
            return
        if latest_version.app_info_id != self.pk:
            raise ValidationError({"latest_version": gettext_lazy("Select a release of this platform.")})
        try:
            APP_VERSION_VALIDATOR(self.min_supported_version)
        except ValidationError:
            # NOTE: The field validation shows this error
            return
        if get_app_version_code(self.min_supported_version) > latest_version.version_code:
            raise ValidationError(
                {"min_supported_version": gettext_lazy("Cannot be greater than the latest version.")},
            )

    @property
    def platform_enum(self):
        return AppPlatformEnum(self.platform)

    def get_published_releases(self) -> list["AppRelease"]:
        """Return releases up to the latest version, sorted by version."""
        latest_version = self.latest_version
        if latest_version is None:
            return []
        return sorted(
            (release for release in self.releases.all() if release.version_code <= latest_version.version_code),
            key=lambda release: release.version_code,
        )


class AppRelease(Model):
    """Release notes of a single app version on a platform."""

    app_info_id: int
    app_info = models.ForeignKey[AppInfo, AppInfo](
        AppInfo,
        on_delete=models.CASCADE,
        related_name="releases",
    )
    version = models.CharField[str, str](max_length=20, validators=[APP_VERSION_VALIDATOR])
    updates = models.TextField[str, str](
        blank=True,
        help_text=gettext_lazy("What's new in this version (markdown)."),
    )
    incompatible_changes = models.TextField[str, str](
        blank=True,
        help_text=gettext_lazy("What won't work on older versions after this release (markdown)."),
    )

    class Meta(TypedModelMeta):  # type: ignore[reportIncompatibleVariableOverride]
        unique_together = (
            "app_info",
            "version",
        )

    @typing.override
    def __str__(self):
        return self.version

    @property
    def version_code(self) -> int:
        return get_app_version_code(self.version)

    @property
    def firebase_key(self) -> str:
        # NOTE: Firebase keys cannot contain "."
        return self.version.replace(".", "_")

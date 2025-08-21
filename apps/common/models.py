# pyright: reportUninitializedInstanceVariable=false
import typing

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy
from django_choices_field import IntegerChoicesField
from django_stubs_ext.db.models import TypedModelMeta
from ulid import ULID

from apps.user.models import User
from main.db import Model
from utils.common import validate_ulid


class FirebasePushStatusEnum(models.IntegerChoices):
    PENDING = 1, "Pending"
    PROCESSING = 2, "Processing"
    SUCCESS = 3, "Success"
    FAILED = 4, "Failed"


class UploadHelper:
    @staticmethod
    def common_asset(instance: "CommonAsset", filename: str):
        return f"common/asset/{instance.type}/{ULID()!s}/{filename}"


# -- Abstracts
class UserResource(Model):
    # FIXME(tnagorra): Should users be able to edit this?
    client_id = models.CharField(
        null=False,
        blank=False,
        unique=True,
        max_length=26,
        validators=[validate_ulid],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    created_by: User = models.ForeignKey(  # type: ignore[reportIncompatibleVariableOverride]
        User,
        related_name="%(class)s_created",
        on_delete=models.PROTECT,
    )
    modified_by: User = models.ForeignKey(  # type: ignore[reportIncompatibleVariableOverride]
        User,
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
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by: User = models.ForeignKey(  # type: ignore[reportIncompatibleVariableOverride]
        User,
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
    # NOTE: We should not directly use old_id. This is ID reference to old system
    old_id = models.CharField(max_length=30, db_index=True, null=True, blank=True)

    firebase_id = models.CharField(max_length=30, unique=True, default=ULID)

    firebase_push_status: int | None = IntegerChoicesField(  # type: ignore[reportAssignmentType]
        choices_enum=FirebasePushStatusEnum,
        null=True,
        blank=True,
    )
    firebase_last_pushed = models.DateTimeField(
        null=True,
        blank=True,
        help_text=gettext_lazy("The latest time when resource was pushed to firebase"),
    )

    # FIXME(tnagorra): Override create and update to set FirebasePushStatusEnum.PENDING

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
    firebase_id = models.CharField(max_length=30, unique=True)

    firebase_last_pulled = models.DateTimeField(
        null=True,
        blank=True,
        help_text=gettext_lazy("The latest time when resource was pulled from firebase"),
    )

    class Meta(TypedModelMeta):  # type: ignore[reportIncompatibleVariableOverride]
        abstract = True


class AssetMimetypeEnum(models.IntegerChoices):
    GEOJSON = 100, "application/geo+json"
    JSON = 101, "application/json"

    IMAGE_JPEG = 201, "image/jpeg"
    IMAGE_PNG = 202, "image/png"
    IMAGE_GIF = 203, "image/gif"

    GZIP = 300, "application/x-gzip"

    CSV = 400, "text/csv"

    @classmethod
    def get_display(cls, value: typing.Self | int) -> str:
        if value in cls:
            return str(cls(value).label)
        return "Unknown"

    @classmethod
    def is_valid_mimetype(cls, mimetype: str) -> bool:
        """
        Check if the given mimetype is valid for project assets.
        """
        return mimetype in [choice.label for choice in cls]

    @classmethod
    def get_mimetype_by_label(cls, label: str) -> typing.Self | None:
        for choice in cls:
            if choice.label == label:
                return choice
        return None


# FIXME(tnagorra): Finalize the enum labels
class AssetTypeEnum(models.IntegerChoices):
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
    Mimetype = AssetMimetypeEnum
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # MB
    Type = AssetTypeEnum

    type = IntegerChoicesField(
        choices_enum=AssetTypeEnum,
    )

    mimetype = IntegerChoicesField(
        choices_enum=AssetMimetypeEnum,
        null=True,
        blank=True,
    )

    file_size = models.PositiveIntegerField(
        help_text=gettext_lazy("The size of the file in bytes"),
    )

    marked_as_deleted = models.BooleanField(
        default=False,
        help_text=gettext_lazy("If this flag is enabled, this asset will be deleted in the future"),
    )

    file = models.FileField(
        upload_to=UploadHelper.common_asset,
        help_text=gettext_lazy("The file associated with the asset"),
        null=True,
        blank=True,
    )

    external_url = models.CharField(
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
        """Returns objects that are mot marked for deletion"""
        return cls.objects.filter(marked_as_deleted=False)

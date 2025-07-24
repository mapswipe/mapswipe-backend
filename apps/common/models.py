# pyright: reportUninitializedInstanceVariable=false
import typing

from django.db import models
from django.utils.translation import gettext_lazy
from django_choices_field import IntegerChoicesField
from django_stubs_ext.db.models import TypedModelMeta

from apps.user.models import User
from main.db import Model
from utils.common import validate_ulid


class FirebasePushStatusEnum(models.IntegerChoices):
    PENDING = 1, "Pending"
    PROCESSING = 2, "Processing"
    SUCCESS = 3, "Success"
    FAILED = 4, "Failed"


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
    created_by = models.ForeignKey(
        User,
        related_name="%(class)s_created",
        on_delete=models.PROTECT,
    )
    modified_by = models.ForeignKey(
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
    archived_by = models.ForeignKey(
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


class FirebaseResource(Model):
    firebase_push_status: int | None = IntegerChoicesField(  # type: ignore[reportAssignmentType]
        choices_enum=FirebasePushStatusEnum,
        null=True,
        blank=True,
    )
    firebase_last_pushed = models.DateTimeField(
        null=True,
        blank=True,
        help_text=gettext_lazy("The latest time when project was pushed to firebase"),
    )

    @property
    def firebase_push_status_enum(self):
        if self.firebase_push_status:
            return FirebasePushStatusEnum(self.firebase_push_status)
        return None

    def update_firebase_push_status(self, firebase_push_status: FirebasePushStatusEnum, *, commit: bool = True):
        self.firebase_push_status = firebase_push_status
        if commit:
            self.save(update_fields=("firebase_push_status",))

    class Meta(TypedModelMeta):  # type: ignore[reportIncompatibleVariableOverride]
        abstract = True

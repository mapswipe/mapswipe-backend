# pyright: reportUninitializedInstanceVariable=false
import typing

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext
from django_stubs_ext.db.models import TypedModelMeta
from ulid import ULID

from apps.user.models import User
from main.db import Model


def validate_ulid(val: str):
    try:
        ULID.from_str(val)
    except (ValueError, TypeError) as e:
        raise ValidationError(
            gettext("Not a valid ULID value '%s'") % (val),
        ) from e


def get_ulid_str():
    return str(ULID())


# -- Abstracts
class UserResource(Model):
    client_id = models.CharField(
        unique=True,
        max_length=26,
        editable=False,
        default=get_ulid_str,
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

# pyright: reportUninitializedInstanceVariable=false
import typing

from django.db import models
from django_stubs_ext.db.models import TypedModelMeta

from apps.user.models import User
from main.db import Model
from utils.common import validate_ulid


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

from django.db import models

from apps.user.models import User


# -- Abstracts
class UserResource(models.Model):
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
    pk: int
    created_by_id: int
    modified_by_id: int

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        abstract = True
        ordering = ["-id"]

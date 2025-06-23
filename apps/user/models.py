import typing

# from __future__ import annotations
from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import CustomUserManager


class User(AbstractUser):
    EMAIL_FIELD = USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    username = None
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=255)
    # FIXME(tnagorra): We might need to skip the indexing
    old_id = models.CharField(max_length=30, db_index=True, null=True)

    objects: CustomUserManager = CustomUserManager()  # type: ignore[reportAssignmentType]

    @typing.override
    def save(self, *args, **kwargs):
        # Make sure email are same and lowercase
        self.email = self.email.lower()
        if self.pk is None:
            super().save(*args, **kwargs)
            # Remove force_insert since we have already inserted
            kwargs.pop("force_insert", None)
        self.display_name = self.get_full_name() or f"User#{self.pk}"
        return super().save(*args, **kwargs)

# pyright: reportUninitializedInstanceVariable=false
import typing

# from __future__ import annotations
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext

from .managers import CustomUserManager


class User(AbstractUser):
    EMAIL_FIELD = USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    username = None
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=255)
    # FIXME(tnagorra): We might need to skip the indexing
    # TODO(tnagorra): Rename this to firebase_userid

    contributor_user = models.ForeignKey(
        "contributor.ContributorUser",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        unique=True,
        help_text=gettext(
            "The Contributor user associated with this User. This will also be used for authentication using firebase.",
        ),
    )

    objects: CustomUserManager = CustomUserManager()  # type: ignore[reportAssignmentType]

    # type hints
    pk: int
    contributor_user_id: int | None

    @property
    def anonymize_email(self):
        email_name, email_domain = self.email.split("@")
        email_name_first_char, email_name_last_char = email_name[:1], email_name[-1:]
        return f"{email_name_first_char}***{email_name_last_char}@{email_domain}"

    @property
    def firebase_id(self) -> str | None:
        """
        Return linked contributor user's firebase ID
        NOTE: N+1 issue
        """
        if self.contributor_user_id:
            return self.contributor_user.firebase_id
        return None

    @typing.override
    def save(self, *args, **kwargs):
        # Make sure email are same and lowercase
        self.email = self.email.lower()
        if self.pk is None:  # pyright: ignore [reportUnnecessaryComparison]
            super().save(*args, **kwargs)
            # Remove force_insert since we have already inserted
            kwargs.pop("force_insert", None)
        self.display_name = self.get_full_name() or f"User#{self.pk}"
        return super().save(*args, **kwargs)

# pyright: reportUninitializedInstanceVariable=false
import typing

# from __future__ import annotations
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext

from .managers import CustomUserManager

if typing.TYPE_CHECKING:
    from apps.contributor.models import ContributorUser  # noqa: F401


class User(AbstractUser):
    """Custom user model with email as unique identifier.

    The user is linked to a contributor user, which holds user information synced from firebase.
    This mapping is essential to integrate Firebase authentication this system.
    Additionally, the mapping ensures that data created or updated in this system
    can be accurately synchronized back to Firebase with the correct user association.
    """

    EMAIL_FIELD = USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    username = None
    email = models.EmailField[str, str](unique=True)
    display_name = models.CharField[str, str](max_length=255)
    # FIXME(tnagorra): We might need to skip the indexing
    # TODO(tnagorra): Rename this to firebase_userid

    # TODO: change this to one-to-one field
    contributor_user = models.ForeignKey["ContributorUser", "ContributorUser"](
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
        """Get linked contributor user's firebase ID.

        NOTE: N+1 issue
        """
        if self.contributor_user_id:
            return self.contributor_user.firebase_id
        return None

    @classmethod
    def get_bot_user(cls) -> typing.Self:
        return cls.objects.get_or_create(
            email="bot@mapswipe.org",
            defaults=dict(
                first_name="Mapswipe",
                last_name="Bot",
            ),
        )[0]

    @typing.override
    def save(self, *args, **kwargs):
        # Make sure email are same and lowercase
        self.email = self.email.lower()
        if self.pk is None:  # type: ignore[reportUnnecessaryComparison]
            super().save(*args, **kwargs)
            # Remove force_insert since we have already inserted
            kwargs.pop("force_insert", None)
        self.display_name = self.get_full_name() or f"User#{self.pk}"
        return super().save(*args, **kwargs)

import typing

from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.common.models import Announcement
from apps.user.models import User
from main.config import Config
from main.tests import TestCase


class MockRequest(typing.NamedTuple):
    user: User


class TestAnnouncement(TestCase):
    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a superuser for admin login
        User = get_user_model()
        cls.admin_user = User.objects.create_superuser(  # type: ignore[reportAttributeAccessIssue]
            email="admin@example.com",
            password="password123",  # noqa: S106
        )

    def test_create_announcement(self):
        request = MockRequest(user=self.admin_user)
        self.force_login(request.user)

        url = reverse("admin:common_announcement_add")

        announcement_ref = self.firebase_helper.ref(
            Config.FirebaseKeys.announcement(),
        )

        data = {
            "client_id": "01K44YMVYTKY1R3906XW3QQK05",
            "text": "We have a new release v1.2.3",
            "is_active": True,
            "url": "https://play.google.com/store/apps/details?id=org.missingmaps.mapswipe",
            "created_by": self.admin_user.id,
            "modified_by": self.admin_user.id,
        }

        # Post to admin add form
        response = self.client.post(url, data, follow=True)
        assert response.status_code == 200

        announcement_1 = Announcement.objects.get(text="We have a new release v1.2.3")
        assert announcement_1.is_active
        assert announcement_1.url == "https://play.google.com/store/apps/details?id=org.missingmaps.mapswipe"

        firebase_announcement: typing.Any = announcement_ref.get()
        assert firebase_announcement is not None
        assert firebase_announcement.get("url") == "https://play.google.com/store/apps/details?id=org.missingmaps.mapswipe"

        # test active only one announcement at once
        data = {
            "client_id": "01K44ZF3KMS6GV2AD93EG6WP9X",
            "text": "Checkout the latest blog post about airstrips",
            "is_active": True,
            "url": "https://mapswipe.org/en/blogs/2025-04-03-papua-new-guinea-swiping-to-find-airstrips",
            "created_by": self.admin_user.id,
            "modified_by": self.admin_user.id,
        }

        # Post to admin add form
        response = self.client.post(url, data, follow=True)
        assert response.status_code == 200

        announcement_2 = Announcement.objects.get(text="Checkout the latest blog post about airstrips")
        assert announcement_2.is_active
        assert announcement_2.url == "https://mapswipe.org/en/blogs/2025-04-03-papua-new-guinea-swiping-to-find-airstrips"

        firebase_announcement: typing.Any = announcement_ref.get()
        assert firebase_announcement is not None
        assert (
            firebase_announcement.get("url")
            == "https://mapswipe.org/en/blogs/2025-04-03-papua-new-guinea-swiping-to-find-airstrips"
        )

        # check only one active announcement
        assert Announcement.objects.filter(is_active=True).count() == 1

        # check if current announcement is active
        announcement_1.refresh_from_db()
        assert not announcement_1.is_active

        # test announcement de-activation
        url = reverse("admin:common_announcement_change", args=[announcement_2.pk])
        data = {
            "client_id": "01K44ZF3KMS6GV2AD93EG6WP9X",
            "text": "Checkout the latest blog post about airstrips",
            "is_active": False,
            "url": "https://mapswipe.org/en/blogs/2025-04-03-papua-new-guinea-swiping-to-find-airstrips",
            "created_by": self.admin_user.id,
            "modified_by": self.admin_user.id,
        }
        response = self.client.post(url, data, follow=True)
        assert response.status_code == 200

        firebase_announcement: typing.Any = announcement_ref.get()
        assert firebase_announcement is None

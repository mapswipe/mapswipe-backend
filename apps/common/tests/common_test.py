import typing

from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.common.models import Announcement
from apps.user.models import User
from main.tests import TestCase


class MockRequest(typing.NamedTuple):
    user: User


class TestAnnouncement(TestCase):
    @typing.override
    def setUp(self):
        # Create a superuser for admin login
        User = get_user_model()
        self.admin_user = User.objects.create_superuser(  # type: ignore[reportAttributeAccessIssue]
            email="admin@example.com",
            password="password123",  # noqa: S106
        )
        self.client.login(email="admin@example.com", password="password123")  # noqa: S106

    def test_create_announcement(self):
        url = reverse("admin:common_announcement_add")

        data = {
            "client_id": "01K44YMVYTKY1R3906XW3QQK05",
            "text": "Announcement",
            "is_active": True,
            "url": "https://example.com",
            "created_by": self.admin_user.id,
            "modified_by": self.admin_user.id,
        }

        # Post to admin add form
        response = self.client.post(url, data, follow=True)
        assert response.status_code == 200

        announcement_1 = Announcement.objects.get(text="Announcement")
        assert announcement_1.is_active
        assert announcement_1.url == "https://example.com"

        # test active only one announcement at once
        data = {
            "client_id": "01K44ZF3KMS6GV2AD93EG6WP9X",
            "text": "Announcement Active",
            "is_active": True,
            "url": "https://example2.com",
            "created_by": self.admin_user.id,
            "modified_by": self.admin_user.id,
        }

        # Post to admin add form
        response = self.client.post(url, data, follow=True)
        assert response.status_code == 200

        announcement_2 = Announcement.objects.get(text="Announcement Active")
        assert announcement_2.is_active
        assert announcement_2.url == "https://example2.com"

        # check only one active announcement
        assert Announcement.objects.filter(is_active=True).count() == 1
        announcement_1.refresh_from_db()

        # check if other announcements are inactive
        assert not announcement_1.is_active

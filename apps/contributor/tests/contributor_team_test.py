import typing
from uuid import uuid4

import pytest
from django.contrib.admin.sites import AdminSite
from django.core.exceptions import ValidationError
from django.urls import reverse
from ulid import ULID

from apps.contributor.admin import ContributorTeamAdmin
from apps.contributor.factories import ContributorTeamFactory, ContributorUserFactory
from apps.contributor.models import ContributorTeam
from apps.user.factories import UserFactory
from apps.user.models import User
from main.config import Config
from main.tests import TestCase


class MockRequest(typing.NamedTuple):
    user: User


class TestContributorTeam(TestCase):
    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory.create()
        cls.user_resource_kwargs = dict(
            created_by=cls.user,
            modified_by=cls.user,
        )
        cls.site = AdminSite()
        cls.admin = ContributorTeamAdmin(ContributorTeam, cls.site)
        cls.contributor_team = ContributorTeamFactory.create(**cls.user_resource_kwargs)
        cls.contributor_user = ContributorUserFactory.create(
            firebase_id="test_id",
            team=cls.contributor_team,
        )
        # Create superuser for admin login
        cls.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass",  # noqa: S106
        )

    def test_cannot_archive_team_with_members(self):
        self.contributor_team.is_archived = True
        with pytest.raises(ValidationError):
            self.contributor_team.clean()

    def test_archive_team(self):
        request = MockRequest(user=self.user)
        self.force_login(request.user)
        self.contributor_user.delete()
        self.contributor_team.is_archived = True
        self.admin.save_model(request, self.contributor_team, form=None, change=True)
        assert self.contributor_team.is_archived is True
        assert self.contributor_team.archived_by == self.user

    def test_cannot_add_member_to_archived_team(self):
        self.contributor_team.is_archived = True
        self.contributor_team.save(update_fields=["is_archived"])
        self.contributor_user.team = self.contributor_team
        with pytest.raises(ValidationError):
            self.contributor_user.clean()

    def test_add_to_firebase(self):
        self.client.login(email="admin@example.com", password="adminpass")  # noqa: S106

        # Get admin add URL
        url = reverse("admin:contributor_contributorteam_add")

        client_id = str(ULID())
        token = str(uuid4())
        data = {
            "client_id": client_id,
            "created_by": self.user.pk,
            "modified_by": self.user.pk,
            "name": "Test team",
            "token": token,
        }
        response = self.client.post(url, data, follow=True)
        assert response.status_code == 200

        # Verify object actually created
        team = ContributorTeam.objects.get(name="Test team")
        firebase_id = team.firebase_id

        contributor_team_ref = self.firebase_helper.ref(
            Config.FirebaseKeys.contributor_team(firebase_id),
        )

        # Check if team created in firebase
        firebase_contributor_team: typing.Any = contributor_team_ref.get()
        assert firebase_contributor_team is not None
        assert firebase_contributor_team.get("teamName") == "Test team"

        # Update team
        url = reverse("admin:contributor_contributorteam_change", args=[team.pk])
        data = {
            "client_id": client_id,
            "created_by": self.user.pk,
            "modified_by": self.user.pk,
            "name": "Test team updated",
            "token": token,
        }

        response = self.client.post(url, data, follow=True)
        assert response.status_code == 200

        # Check if team updated in database
        team.refresh_from_db()
        assert team.name == "Test team updated"

        # Check if team updated in firebase
        firebase_contributor_team: typing.Any = contributor_team_ref.get()
        assert firebase_contributor_team is not None
        assert firebase_contributor_team.get("teamName") == "Test team updated"

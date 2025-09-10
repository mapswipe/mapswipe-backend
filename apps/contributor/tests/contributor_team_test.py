import typing

import pytest
from django.contrib.admin.sites import AdminSite
from django.core.exceptions import ValidationError
from django.urls import reverse

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
    def setUp(self):
        self.firebase_helper = Config.FIREBASE_HELPER
        self.user = UserFactory.create()
        self.user_resource_kwargs = dict(
            created_by=self.user,
            modified_by=self.user,
        )
        self.site = AdminSite()
        self.admin = ContributorTeamAdmin(ContributorTeam, self.site)
        self.contributor_team = ContributorTeamFactory.create(**self.user_resource_kwargs)
        self.contributor_user = ContributorUserFactory.create(
            firebase_id="test_id",
            team=self.contributor_team,
        )
        # Create superuser for admin login
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass",  # noqa: S106
        )
        self.client.login(email="admin@example.com", password="adminpass")  # noqa: S106

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
        # Get admin add URL
        url = reverse("admin:contributor_contributorteam_add")

        data = {
            "client_id": "01K4SB39VDFA0D4KG6MDZ0X312",
            "created_by": self.user.pk,
            "modified_by": self.user.pk,
            "name": "Test team",
            "token": "2aa49fb4-5b55-47ab-8e03-426d3228338e",
        }

        response = self.client.post(url, data, follow=True)
        assert response.status_code == 200

        # Verify object actually created
        team = ContributorTeam.objects.get(name="Test team")

        # Check if team created in firebase
        firebase_id = ContributorTeam.objects.get(id=team.pk).firebase_id

        contributor_team_ref = self.firebase_helper.ref(
            Config.FirebaseKeys.contributor_team(firebase_id),
        )
        firebase_contributor_team: typing.Any = contributor_team_ref.get()
        assert firebase_contributor_team is not None
        assert firebase_contributor_team.get("teamName") == "Test team"

        # Update
        url = reverse("admin:contributor_contributorteam_change", args=[team.pk])
        data = {
            "client_id": "01K4SB39VDFA0D4KG6MDZ0X312",
            "created_by": self.user.pk,
            "modified_by": self.user.pk,
            "name": "Test team updated",
            "token": "2aa49fb4-5b55-47ab-8e03-426d3228338e",
        }

        response = self.client.post(url, data, follow=True)
        assert response.status_code == 200
        team.refresh_from_db()

        assert team.name == "Test team updated"

        # Check if team updated in firebase
        firebase_contributor_team = contributor_team_ref.get()
        assert firebase_contributor_team is not None
        assert firebase_contributor_team.get("teamName") == "Test team updated"

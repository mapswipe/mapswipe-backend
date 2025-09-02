import typing

import pytest
from django.contrib.admin.sites import AdminSite
from django.core.exceptions import ValidationError

from apps.contributor.admin import ContributorTeamAdmin
from apps.contributor.factories import ContributorTeamFactory, ContributorUserFactory
from apps.contributor.models import ContributorTeam
from apps.user.factories import UserFactory
from apps.user.models import User
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

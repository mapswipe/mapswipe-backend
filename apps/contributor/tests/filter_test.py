import typing

from apps.contributor.factories import (
    ContributorTeamFactory,
    ContributorUserFactory,
    ContributorUserGroupFactory,
    ContributorUserGroupMembershipFactory,
)
from apps.user.factories import UserFactory
from main.tests import TestCase


class TestContributorFilters(TestCase):
    class Query:
        CONTRIBUTOR_USERS = """
            query ContributorUsers($filters: ContributorUserFilter) {
              contributorUsers(filters: $filters) {
                totalCount
                results {
                  id
                }
              }
            }
        """

        CONTRIBUTOR_USER_GROUPS = """
            query ContributorUserGroups($filters: ContributorUserGroupFilter, $includeAll: Boolean) {
              contributorUserGroups(filters: $filters, includeAll: $includeAll) {
                totalCount
                results {
                  id
                }
              }
            }
        """

        CONTRIBUTOR_USER_GROUP_MEMBERS = """
            query ContributorUserGroupMembers($filters: ContributorUserGroupMembershipFilter) {
              contributorUserGroupMembers(filters: $filters) {
                totalCount
                results {
                  id
                }
              }
            }
        """

        CONTRIBUTOR_TEAMS = """
            query ContributorTeams($filters: ContributorTeamFilter, $includeAll: Boolean) {
              contributorTeams(filters: $filters, includeAll: $includeAll) {
                totalCount
                results {
                  id
                }
              }
            }
        """

    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory.create()
        cls.user_resource_kwargs = dict(
            created_by=cls.user,
            modified_by=cls.user,
        )

        cls.team1 = ContributorTeamFactory.create(**cls.user_resource_kwargs, name="Alpha Team")
        cls.team2 = ContributorTeamFactory.create(**cls.user_resource_kwargs, name="Beta Team", is_archived=True)

        cls.contributor_user1 = ContributorUserFactory.create(username="john", team=cls.team1)
        cls.contributor_user2 = ContributorUserFactory.create(username="jane")

        cls.user_group1 = ContributorUserGroupFactory.create(**cls.user_resource_kwargs, name="Mappers Nepal")
        cls.user_group2 = ContributorUserGroupFactory.create(
            **cls.user_resource_kwargs,
            name="Mappers Kenya",
            is_archived=True,
        )

        cls.membership1 = ContributorUserGroupMembershipFactory.create(
            user_group=cls.user_group1,
            user=cls.contributor_user1,
        )
        cls.membership2 = ContributorUserGroupMembershipFactory.create(
            user_group=cls.user_group2,
            user=cls.contributor_user2,
        )

    # Contributor users
    def test_contributor_user_filter_by_firebase_id(self):
        self.force_login(self.user)
        content = self.query_check(
            self.Query.CONTRIBUTOR_USERS,
            variables={"filters": {"firebaseId": {"exact": self.contributor_user1.firebase_id}}},
        )
        assert content["data"]["contributorUsers"]["totalCount"] == 1
        assert content["data"]["contributorUsers"]["results"][0]["id"] == self.gID(self.contributor_user1.pk)

    def test_contributor_user_filter_by_username(self):
        self.force_login(self.user)
        content = self.query_check(
            self.Query.CONTRIBUTOR_USERS,
            variables={"filters": {"username": {"exact": "jane"}}},
        )
        assert content["data"]["contributorUsers"]["totalCount"] == 1
        assert content["data"]["contributorUsers"]["results"][0]["id"] == self.gID(self.contributor_user2.pk)

    def test_contributor_user_filter_by_team(self):
        self.force_login(self.user)
        content = self.query_check(
            self.Query.CONTRIBUTOR_USERS,
            variables={"filters": {"teamId": {"exact": self.gID(self.team1.pk)}}},
        )
        assert content["data"]["contributorUsers"]["totalCount"] == 1
        assert content["data"]["contributorUsers"]["results"][0]["id"] == self.gID(self.contributor_user1.pk)

    # User groups
    def test_user_group_filter_by_firebase_id(self):
        self.force_login(self.user)
        content = self.query_check(
            self.Query.CONTRIBUTOR_USER_GROUPS,
            variables={"filters": {"firebaseId": {"exact": self.user_group1.firebase_id}}},
        )
        assert content["data"]["contributorUserGroups"]["totalCount"] == 1
        assert content["data"]["contributorUserGroups"]["results"][0]["id"] == self.gID(self.user_group1.pk)

    def test_user_group_filter_by_name(self):
        self.force_login(self.user)
        content = self.query_check(
            self.Query.CONTRIBUTOR_USER_GROUPS,
            variables={"filters": {"name": "mappers"}, "includeAll": True},
        )
        assert content["data"]["contributorUserGroups"]["totalCount"] == 2

        content = self.query_check(
            self.Query.CONTRIBUTOR_USER_GROUPS,
            variables={"filters": {"name": "Mappers Nepal"}},
        )
        assert content["data"]["contributorUserGroups"]["totalCount"] == 1
        assert content["data"]["contributorUserGroups"]["results"][0]["id"] == self.gID(self.user_group1.pk)

    def test_user_group_filter_by_is_archived(self):
        self.force_login(self.user)
        content = self.query_check(
            self.Query.CONTRIBUTOR_USER_GROUPS,
            variables={"filters": {"isArchived": {"exact": True}}, "includeAll": True},
        )
        assert content["data"]["contributorUserGroups"]["totalCount"] == 1
        assert content["data"]["contributorUserGroups"]["results"][0]["id"] == self.gID(self.user_group2.pk)

    def test_user_group_filter_by_user_firebase_id(self):
        self.force_login(self.user)
        content = self.query_check(
            self.Query.CONTRIBUTOR_USER_GROUPS,
            variables={"filters": {"userFirebaseId": self.contributor_user1.firebase_id}},
        )
        assert content["data"]["contributorUserGroups"]["totalCount"] == 1
        assert content["data"]["contributorUserGroups"]["results"][0]["id"] == self.gID(self.user_group1.pk)

    # User group memberships
    def test_user_group_membership_filter_by_user_group(self):
        self.force_login(self.user)
        content = self.query_check(
            self.Query.CONTRIBUTOR_USER_GROUP_MEMBERS,
            variables={"filters": {"userGroupId": {"exact": self.gID(self.user_group2.pk)}}},
        )
        assert content["data"]["contributorUserGroupMembers"]["totalCount"] == 1
        assert content["data"]["contributorUserGroupMembers"]["results"][0]["id"] == self.gID(self.membership2.pk)

    # Teams
    def test_team_filter_by_firebase_id(self):
        self.force_login(self.user)
        content = self.query_check(
            self.Query.CONTRIBUTOR_TEAMS,
            variables={"filters": {"firebaseId": {"exact": self.team1.firebase_id}}},
        )
        assert content["data"]["contributorTeams"]["totalCount"] == 1
        assert content["data"]["contributorTeams"]["results"][0]["id"] == self.gID(self.team1.pk)

    def test_team_filter_by_name(self):
        self.force_login(self.user)
        content = self.query_check(
            self.Query.CONTRIBUTOR_TEAMS,
            variables={"filters": {"name": "team"}, "includeAll": True},
        )
        assert content["data"]["contributorTeams"]["totalCount"] == 2

        content = self.query_check(
            self.Query.CONTRIBUTOR_TEAMS,
            variables={"filters": {"name": "Alpha Team"}},
        )
        assert content["data"]["contributorTeams"]["totalCount"] == 1
        assert content["data"]["contributorTeams"]["results"][0]["id"] == self.gID(self.team1.pk)

    def test_team_filter_by_is_archived(self):
        self.force_login(self.user)
        content = self.query_check(
            self.Query.CONTRIBUTOR_TEAMS,
            variables={"filters": {"isArchived": {"exact": True}}, "includeAll": True},
        )
        assert content["data"]["contributorTeams"]["totalCount"] == 1
        assert content["data"]["contributorTeams"]["results"][0]["id"] == self.gID(self.team2.pk)

import typing
from pathlib import Path

from ulid import ULID

from apps.user.factories import UserFactory
from main.tests import TestCase

BASE_DIR = Path(__file__).resolve().parent


class TestContributorUserGroupMutation(TestCase):
    class Mutation:
        CREATE_CONTRIBUTOR_USER_GROUP = """
        mutation CreateContributorUserGroup($data: ContributorUserGroupCreateInput!) {
            createContributorUserGroup(data: $data) {
                ... on OperationInfo {
                  __typename
                  messages {
                    code
                    field
                    kind
                    message
                  }
                }
                ... on ContributorUserGroupTypeMutationResponseType {
                    errors
                    ok
                    result {
                        id
                        name
                        description
                        clientId
                        isArchived
                    }
                }
            }
        }
        """
        UPDATE_CONTRIBUTOR_USER_GROUP = """
        mutation UpdateContributorUserGroup($data: ContributorUserGroupUpdateInput!, $pk: ID!) {
            updateContributorUserGroup(data: $data, pk: $pk) {
                ... on OperationInfo {
                  __typename
                  messages {
                    code
                    field
                    kind
                    message
                  }
                }
                ... on ContributorUserGroupTypeMutationResponseType {
                    errors
                    ok
                    result {
                        id
                        name
                        description
                        clientId
                        isArchived
                        archivedBy {
                            id
                        }
                    }
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

    def test_contributor_user_group(self):
        contributor_user_group_data = {
            "clientId": str(ULID()),
            "name": "Test User Group",
            "description": "For test purpose only",
        }

        # Creating ContributorUserGroup: Without authentication
        content = self.query_check(
            self.Mutation.CREATE_CONTRIBUTOR_USER_GROUP,
            variables={
                "data": contributor_user_group_data,
            },
        )
        assert content["data"]["createContributorUserGroup"]["messages"] == [
            {
                "code": None,
                "field": "createContributorUserGroup",
                "kind": "PERMISSION",
                "message": "User is not authenticated.",
            },
        ], content

        # Creating ContributorUserGroup: With authentication
        self.force_login(self.user)
        content = self.query_check(
            self.Mutation.CREATE_CONTRIBUTOR_USER_GROUP,
            variables={
                "data": contributor_user_group_data,
            },
        )
        resp_data = content["data"]["createContributorUserGroup"]
        assert resp_data["errors"] is None, content

        # Updating ContributorUserGroup
        content = self.query_check(
            self.Mutation.UPDATE_CONTRIBUTOR_USER_GROUP,
            variables={
                "data": {
                    "name": "Test Contributor User Group",
                    "clientId": resp_data["result"]["clientId"],
                    "isArchived": False,
                },
                "pk": resp_data["result"]["id"],
            },
        )
        resp_data = content["data"]["updateContributorUserGroup"]
        assert resp_data["errors"] is None, content

        # Updating ContributorUserGroup with isArchived
        content = self.query_check(
            self.Mutation.UPDATE_CONTRIBUTOR_USER_GROUP,
            variables={
                "data": {
                    "name": "Test Contributor User Group",
                    "clientId": resp_data["result"]["clientId"],
                    "isArchived": True,
                },
                "pk": resp_data["result"]["id"],
            },
        )
        resp_data = content["data"]["updateContributorUserGroup"]
        assert resp_data["errors"] is None, content
        assert resp_data["result"]["isArchived"] is True, content
        assert resp_data["result"]["archivedBy"]["id"] == self.gID(self.user.pk), content

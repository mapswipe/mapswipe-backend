import typing
from pathlib import Path

from ulid import ULID

from apps.contributor.models import ContributorUserGroup
from apps.user.factories import UserFactory
from main.config import Config
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
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(
                self.Mutation.CREATE_CONTRIBUTOR_USER_GROUP,
                variables={
                    "data": contributor_user_group_data,
                },
            )
        resp_data = content["data"]["createContributorUserGroup"]
        assert resp_data["errors"] is None, content

        user_group = ContributorUserGroup.objects.get(id=resp_data["result"]["id"])
        contributor_user_group_ref = Config.FIREBASE_HELPER.ref(
            Config.FirebaseKeys.contributor_user_group(user_group.firebase_id),
        )
        fb_user_group: typing.Any = contributor_user_group_ref.get()
        assert fb_user_group is not None

        # Updating ContributorUserGroup
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(
                self.Mutation.UPDATE_CONTRIBUTOR_USER_GROUP,
                variables={
                    "data": {
                        "name": "Test Contributor User Group Updated",
                        "clientId": resp_data["result"]["clientId"],
                        "isArchived": False,
                    },
                    "pk": resp_data["result"]["id"],
                },
            )
        resp_data = content["data"]["updateContributorUserGroup"]
        assert resp_data["errors"] is None, content

        fb_user_group: typing.Any = contributor_user_group_ref.get()
        assert fb_user_group is not None
        assert fb_user_group.get("name") == "Test Contributor User Group Updated"

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

import json
import typing
from pathlib import Path

from django.conf import settings

from apps.contributor.models import ContributorUserGroup
from apps.user.factories import UserFactory
from main.config import Config
from main.tests import TestCase


class TestUserGroupE2E(TestCase):
    class Mutation:
        CREATE = """
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
                    ok
                    errors
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
        UPDATE = """
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
                    ok
                    errors
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

    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.firebase_helper = Config.FIREBASE_HELPER
        cls.user = UserFactory.create()
        cls.filename = Path(settings.BASE_DIR) / "test_data" / "usergroup" / "usergroup.json"

    def load_inputs(self) -> list[dict]:
        with self.filename.open("r", encoding="utf-8") as f:
            return json.load(f)

    def test_create_usergroup(self):
        self.force_login(self.user)
        data_list = self.load_inputs()

        for data in data_list:
            with self.captureOnCommitCallbacks(execute=True):
                content = self.query_check(
                    self.Mutation.CREATE,
                    variables={"data": data},
                )

            resp = content["data"]["createContributorUserGroup"]
            assert resp is not None, "GraphQL response is None"
            result = resp["result"]
            assert result["name"] == data["name"]

            firebase_id = ContributorUserGroup.objects.get(id=result["id"]).firebase_id

            contributor_user_group_ref = self.firebase_helper.ref(
                Config.FirebaseKeys.contributor_user_group(firebase_id),
            )
            contributor_user_group_data = contributor_user_group_ref.get()
            assert contributor_user_group_data is not None, "firebase data is None"
            assert type(contributor_user_group_data) is dict, "firebase data is not dict"
            assert data["name"] == contributor_user_group_data["name"]

            # test update
            data["clientId"] = result["clientId"]
            data["name"] = f"{data['name']} Updated"
            with self.captureOnCommitCallbacks(execute=True):
                content = self.query_check(
                    self.Mutation.UPDATE,
                    variables={"data": data, "pk": result["id"]},
                )

            resp = content["data"]["updateContributorUserGroup"]
            assert resp is not None, "GraphQL response is None"
            result = resp["result"]
            assert result["name"] == data["name"]

            contributor_user_group_data = contributor_user_group_ref.get()
            assert contributor_user_group_data is not None, "firebase data is None"
            assert type(contributor_user_group_data) is dict, "firebase data is not dict"
            assert data["name"] == contributor_user_group_data["name"]

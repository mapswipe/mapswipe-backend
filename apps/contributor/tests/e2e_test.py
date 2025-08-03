import typing
import json
from pathlib import Path

from apps.user.factories import UserFactory
from main.tests import TestCase

BASE_DIR = Path(__file__).resolve().parent


class TestContributorUserGroupE2E(TestCase):
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

    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory.create()
        cls.filename = BASE_DIR / "data" / "contributor_user_group.json"

    def load_inputs(self) -> list[dict]:
        with (self.filename).open("r", encoding="utf-8") as f:
            return json.load(f)

    def test_create_contributor_user_group(self):
        self.force_login(self.user)
        data_list = self.load_inputs()

        for data in data_list:
            content = self.query_check(
                self.Mutation.CREATE,
                variables={"data": data},
            )
            result = content["data"]["createContributorUserGroup"]["result"]
            assert result["name"] == data["name"]

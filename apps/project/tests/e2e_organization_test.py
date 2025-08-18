import json
import typing
from pathlib import Path

from apps.user.factories import UserFactory
from main.tests import TestCase

BASE_DIR = Path(__file__).resolve().parent


class Mutation:
    CREATE = """
    mutation CreateOrganization($data: OrganizationCreateInput!) {
        createorganizationinput(data: $data) {
            ... on OperationInfo {
                __typename
                messages {
                    code
                    field
                    kind
                    message
                }
            }
            ... on OrganizationTypeMutationResponseType {
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


class TestOrganization(TestCase):
    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory.create()
        cls.filename = BASE_DIR / "test_data" / "organization" / "data.json"

    def load_inputs(self) -> list[dict]:
        with self.filename.open("r", encoding="utf-8") as f:
            return json.load(f)

    def test_create_organization(self):
        self.force_login(self.user)
        data_list = self.load_inputs()

        for data in data_list:
            content = self.query_check(
                self.Mutation.CREATE,
                variables={"data": data},
            )
            result = content["data"]["createorganizationinput"]["result"]
            assert result["name"] == data["name"]




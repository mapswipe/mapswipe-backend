import json
import typing
from pathlib import Path

import pytest
from django.conf import settings

from apps.user.factories import UserFactory
from main.tests import TestCase


class TestOrganizationE2E(TestCase):
    class Mutation:
        CREATE = """
        mutation CreateOrganization($data: OrganizationCreateInput!) {
            createOrganization(data: $data) {
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

    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory.create()
        # settings.BASE_DIR points to project root
        cls.filename = Path(settings.BASE_DIR) / "test_data" / "organization" / "data.json"

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

            # Ensure the GraphQL response is not None
            resp = content["data"].get("createOrganization")
            if resp is None:
                pytest.fail(f"GraphQL returned null: {content}")

            # Ensure the mutation result is present
            if resp.get("result") is None:
                pytest.fail(f"CreateOrganization failed with response: {resp}")

            result = resp["result"]
            assert result["name"] == data["name"]

import typing
from pathlib import Path

import json5
from django.conf import settings

from apps.user.factories import UserFactory
from main.tests import TestCase


class TestOrganizationE2E(TestCase):
    class Mutation:
        CREATE_ORGANIZATION = """
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
                    }
                }
            }
        }
        """

        UPDATE_ORGANIZATION = """
        mutation UpdateOrganization($data: OrganizationUpdateInput!, $pk: ID!) {
            updateOrganization(data: $data, pk: $pk) {
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
                        clientId
                        description
                        abbreviation
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
        cls.filename = Path(settings.BASE_DIR) / "assets" / "tests" / "organization" / "data.json5"

    def test_organization_e2e(self):
        self._test_organization_service(self.filename)

    def _test_organization_service(self, filename: Path):
        self.force_login(self.user)

        # Load test data from JSON5
        with filename.open("r", encoding="utf-8") as f:
            test_data = json5.load(f)

        create_data_list = test_data["create_organization"]
        update_data_list = test_data["update_organization"]

        for create_data, update_data in zip(create_data_list, update_data_list, strict=False):
            # Create Organization
            organization_content = self.query_check(
                self.Mutation.CREATE_ORGANIZATION,
                variables={"data": create_data},
            )

            create_resp = organization_content["data"].get("createOrganization")
            assert create_resp is not None, f"CreateOrganization returned null for {create_data}"
            assert create_resp.get("result") is not None, f"CreateOrganization failed: {create_resp}"
            org_id = create_resp["result"]["id"]

            # Assert create response matches input
            result_create = create_resp["result"]
            assert result_create["name"] == create_data["name"]
            assert result_create["description"] == create_data["description"]
            assert result_create["clientId"] == create_data["clientId"]

            # Update Organization
            update_content = self.query_check(
                self.Mutation.UPDATE_ORGANIZATION,
                variables={"data": update_data, "pk": org_id},
            )

            update_resp = update_content["data"].get("updateOrganization")
            assert update_resp is not None, f"UpdateOrganization returned null for {update_data}"
            assert update_resp.get("result") is not None, f"UpdateOrganization failed: {update_resp}"

            result_update = update_resp["result"]
            assert result_update["id"] == org_id
            assert result_update["name"] == update_data["name"]
            assert result_update["description"] == update_data["description"]
            assert result_update["clientId"] == update_data["clientId"]
            assert result_update["abbreviation"] == update_data["abbreviation"]
            assert result_update["isArchived"] == update_data["isArchived"]

import typing
from pathlib import Path

import json5

from apps.user.factories import UserFactory
from main.config import Config
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
                        firebaseId
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
                        firebaseId
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

    def test_organization_e2e(self):
        self.force_login(self.user)

        # Load test data from JSON5
        data_file = Path(Config.BASE_DIR, "assets/tests/organization/data.json5")
        with data_file.open("r", encoding="utf-8") as f:
            test_data_list = json5.load(f)

        for item in test_data_list:
            create_data = item["create"]
            updates_data = item["updates"]
            expected_data = item["expected"]

            # Create Organization
            with self.captureOnCommitCallbacks(execute=True):
                organization_content = self.query_check(
                    self.Mutation.CREATE_ORGANIZATION,
                    variables={"data": create_data},
                )

            create_resp = organization_content["data"].get("createOrganization")
            assert create_resp is not None, "CreateOrganization returned null"
            org_id = create_resp["result"]["id"]
            org_fb_id = create_resp["result"]["firebaseId"]

            # Update Organization
            for update_data in updates_data:
                with self.captureOnCommitCallbacks(execute=True):
                    update_content = self.query_check(
                        self.Mutation.UPDATE_ORGANIZATION,
                        variables={"data": update_data, "pk": org_id},
                    )

                update_resp = update_content["data"]["updateOrganization"]
                assert update_resp is not None, "UpdateOrganization returned null"

            # Check organization in Firebase
            org_fb_ref = self.firebase_helper.ref(f"/v2/organisations/{org_fb_id}")
            org_fb_data = org_fb_ref.get()
            assert org_fb_data is not None, f"Organization {org_fb_id} not found in Firebase"

            # Compare expected vs actual Firebase data
            assert org_fb_data == expected_data, "Differences found between expected and actual org data in firebase."

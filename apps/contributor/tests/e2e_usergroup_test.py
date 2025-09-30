import typing
from datetime import datetime
from pathlib import Path

import json5
from django.conf import settings

from apps.common.utils import remove_object_keys
from apps.contributor.factories import ContributorUserFactory
from apps.user.factories import UserFactory
from main.tests import TestCase


class TestUserGroupE2E(TestCase):
    class Mutation:
        CREATE_USERGROUP = """
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
                        firebaseId
                        isArchived
                    }
                }
            }
        }
        """
        UPDATE_USERGROUP = """
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
                        firebaseId
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
        cls.contributor_user = ContributorUserFactory.create(
            username="Ram Bahadur",
        )

        cls.user = UserFactory.create(
            contributor_user=cls.contributor_user,
        )

    def test_usergroup_e2e(self):
        self.force_login(self.user)

        data_file = Path(settings.BASE_DIR, "assets/tests/usergroup/data.json5")
        with data_file.open("r", encoding="utf-8") as f:
            test_data_list = json5.load(f)

        for item in test_data_list:
            create_data = item["create"]
            updates_data = item["updates"]
            expected_data = item["expected"]

            # Create usergroup
            with self.captureOnCommitCallbacks(execute=True):
                content = self.query_check(
                    self.Mutation.CREATE_USERGROUP,
                    variables={"data": create_data},
                )

            create_resp = content["data"]["createContributorUserGroup"]
            assert create_resp is not None, "CreateContribturoUserGroup returned null"
            usergroup_id = create_resp["result"]["id"]
            usergroup_fb_id = create_resp["result"]["firebaseId"]

            archived = False
            # Update usergroup
            for update_data in updates_data:
                with self.captureOnCommitCallbacks(execute=True):
                    content = self.query_check(
                        self.Mutation.UPDATE_USERGROUP,
                        variables={"data": update_data, "pk": usergroup_id},
                    )

                update_resp = content["data"]["updateContributorUserGroup"]
                assert update_resp is not None, "UpdateContribturoUserGroup returned null"
                archived = update_resp["result"]["isArchived"]

            # Check usergroup in Firebase
            usergroup_fb_ref = self.firebase_helper.ref(f"/v2/userGroups/{usergroup_fb_id}")
            usergroup_fb_data = usergroup_fb_ref.get()
            assert usergroup_fb_data is not None, f"Usergroup {usergroup_fb_id} not found in Firebase"
            assert isinstance(usergroup_fb_data, dict), "Usergroup in firebase should be a dictionary"
            assert usergroup_fb_data["createdAt"] is not None, "Field 'createdAt' should be defined"
            assert datetime.fromtimestamp(usergroup_fb_data["createdAt"] / 1000), (
                "Field 'createdAt' should be a unix timestamp"
            )
            assert usergroup_fb_data["createdBy"] == self.contributor_user.firebase_id, (
                "Field 'createdBy' should match contributor user's firebaseId"
            )

            if archived:
                assert usergroup_fb_data["archivedAt"] is not None, "Field 'archivedAt' should be defined"
                assert datetime.fromtimestamp(usergroup_fb_data["archivedAt"] / 1000), (
                    "Field 'archivedAt' should be a unix timestamp"
                )
                assert usergroup_fb_data["archivedBy"] == self.contributor_user.firebase_id, (
                    "Field 'archivedBy' should match contributor user's firebaseId"
                )

            ignored_usergroup_keys = {"createdAt", "createdBy", "archivedAt", "archivedBy"}
            filtered_usergroup_actual = remove_object_keys(usergroup_fb_data, ignored_usergroup_keys)
            filtered_usergroup_expected = remove_object_keys(expected_data, ignored_usergroup_keys)

            # Compare expected vs actual Firebase data
            assert filtered_usergroup_actual == filtered_usergroup_expected, (
                "Differences found between expected and actual usergroup data in firebase."
            )

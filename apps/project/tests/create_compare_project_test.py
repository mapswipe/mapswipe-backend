import typing
from datetime import datetime
from pathlib import Path

import json5
from django.conf import settings
from ulid import ULID

from apps.common.utils import remove_ignored_keys
from apps.project.factories import OrganizationFactory
from apps.tutorial.factories import TutorialFactory
from apps.tutorial.models import Tutorial
from apps.user.factories import UserFactory
from main.config import Config
from main.tests import TestCase


class TestProjectE2E(TestCase):
    class Mutation:
        CREATE_PROJECT = """
        mutation CreateProject($data: ProjectCreateInput!) {
          createProject(data: $data) {
            ... on OperationInfo {
              __typename
              messages {
                code
                field
                kind
                message
              }
            }
            ... on ProjectTypeMutationResponseType {
              errors
              ok
              result {
                id
              }
            }
          }
        }
        """

        UPDATE_PROJECT = """
        mutation UpdateProject($pk: ID!, $data: ProjectUpdateInput!) {
          updateProject(pk: $pk, data: $data) {
            ... on OperationInfo {
              __typename
              messages {
                code
                field
                kind
                message
              }
            }
            ... on ProjectTypeMutationResponseType {
              errors
              ok
              result {
                id
              }
            }
          }
        }
        """

        UPLOAD_ASSET = """
        mutation CreateProjectAsset($data: ProjectAssetCreateInput!) {
          createProjectAsset(data: $data) {
            ... on OperationInfo {
              __typename
              messages {
                code
                field
                kind
                message
              }
            }
            ... on ProjectAssetTypeMutationResponseType {
              errors
              ok
              result {
                id
                assetTypeSpecifics {
                  ... on AoiGeometryAssetPropertyType {
                    __typename
                  }
                  ... on ObjectImageAssetPropertyType {
                    __typename
                    image {
                      id
                    }
                    annotations {
                      id
                    }
                  }
                }
              }
            }
          }
        }
        """

        UPDATE_PROCESSED_PROJECT = """
        mutation UpdateProcessedProject($pk: ID!, $data: ProcessedProjectUpdateInput!) {
          updateProcessedProject(pk: $pk, data: $data) {
            ... on OperationInfo {
              __typename
              messages {
                code
                field
                kind
                message
              }
            }
            ... on ProjectTypeMutationResponseType {
              errors
              ok
              result {
                id
                firebaseId
              }
            }
          }
        }
        """

        UPDATE_PROJECT_STATUS = """
        mutation UpdateProjectStatus($pk: ID!, $data: ProjectStatusUpdateInput!) {
          updateProjectStatus(pk: $pk, data: $data) {
            ... on OperationInfo {
              __typename
              messages {
                code
                field
                kind
                message
              }
            }
            ... on ProjectTypeMutationResponseType {
              errors
              ok
              result {
                id
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
        cls.user_resource_kwargs = dict(
            created_by=cls.user,
            modified_by=cls.user,
        )

        # Load JSON5 file.
        cls.filename = Path(settings.BASE_DIR) / "assets/tests/projects/compare/create_compare_project.json5"
        with cls.filename.open("r", encoding="utf-8") as f:
            cls.data = json5.load(f)

        # Load image and AOI from jsno5.
        cls.image_filename = Path(settings.BASE_DIR) / cls.data["assets"]["image"]
        cls.aoi_geometry_filename = Path(settings.BASE_DIR) / cls.data["assets"]["aoi"]

    def test_create_project(self):
        self.force_login(self.user)
        data = self.data

        # Load Project data initially.
        create_project_data = data["create_project"]
        organization = OrganizationFactory.create(
            name=create_project_data["requestingOrganization"],
            **self.user_resource_kwargs,
        )
        create_project_data["requestingOrganization"] = organization.id

        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(
                self.Mutation.CREATE_PROJECT,
                variables={"data": create_project_data},
            )

        resp = content["data"]["createProject"]
        assert resp is not None, "GraphQL response is None"
        project_id = resp["result"]["id"]

        # Upload Image file.
        image_asset_data = {
            "clientId": f"{create_project_data['clientId']}",
            "inputType": "COVER_IMAGE",
            "project": project_id,
        }

        with self.image_filename.open("rb") as img_file:
            image_resp = self.query_check(
                self.Mutation.UPLOAD_ASSET,
                variables={"data": image_asset_data},
                files={"imageFile": img_file},
                map={"imageFile": ["variables.data.file"]},
            )
        image_id = image_resp["data"]["createProjectAsset"]["result"]["id"]

        # Upload AOI geometry.
        aoi_asset_data = {
            "clientId": str(ULID()),
            "inputType": "AOI_GEOMETRY",
            "project": project_id,
        }

        with self.aoi_geometry_filename.open("rb") as geo_file:
            aoi_resp = self.query_check(
                self.Mutation.UPLOAD_ASSET,
                variables={"data": aoi_asset_data},
                files={"geoFile": geo_file},
                map={"geoFile": ["variables.data.file"]},
            )
        aoi_id = aoi_resp["data"]["createProjectAsset"]["result"]["id"]

        # Load update_project data and inject asset ids of image and AOI geometry.
        update_project_data = data["update_project"]
        update_project_data["image"] = image_id
        update_project_data["projectTypeSpecifics"]["compare"]["aoiGeometry"] = aoi_id
        update_project_data["requestingOrganization"] = organization.id

        # Run the update mutation.
        with self.captureOnCommitCallbacks(execute=True):
            update_content = self.query_check(
                self.Mutation.UPDATE_PROJECT,
                variables={"pk": project_id, "data": update_project_data},
            )

        update_resp = update_content["data"]["updateProject"]
        assert update_resp is not None, "UpdateProject GraphQL response is None"

        # Load first status update from array i.e. "Marked As Ready".
        update_project_status_1_data = data["update_project_status"][0]
        with self.captureOnCommitCallbacks(execute=True):
            update_project_status_1 = self.query_check(
                self.Mutation.UPDATE_PROJECT_STATUS,
                variables={"pk": project_id, "data": update_project_status_1_data},
            )

        update_project_status_1_resp = update_project_status_1["data"]["updateProjectStatus"]
        assert update_project_status_1_resp is not None, "updateProjectStatus GraphQL response is None"

        # Use factory for tutorial creation.
        # TODO: Use serializers instead of factory.
        tutorial = TutorialFactory.create(
            **self.user_resource_kwargs,
            project_id=project_id,
            status=Tutorial.Status.PUBLISHED,
        )

        # Load update_processed_project data.
        update_processed_project_data = data["update_processed_project"]
        update_processed_project_data["tutorial"] = tutorial.id
        update_processed_project_data["requestingOrganization"] = organization.id

        # Run the update_processed_project mutation.
        with self.captureOnCommitCallbacks(execute=True):
            update_processed_content = self.query_check(
                self.Mutation.UPDATE_PROCESSED_PROJECT,
                variables={"pk": project_id, "data": update_processed_project_data},
            )

        update_processed_resp = update_processed_content["data"]["updateProcessedProject"]
        assert update_processed_resp is not None, "UpdateProcessedProject GraphQL response is None"

        # Load second status update from array i.e., "Published".
        update_project_status_2_data = data["update_project_status"][1]
        with self.captureOnCommitCallbacks(execute=True):
            update_project_status_2 = self.query_check(
                self.Mutation.UPDATE_PROJECT_STATUS,
                variables={"pk": project_id, "data": update_project_status_2_data},
            )

        update_project_status_2_resp = update_project_status_2["data"]["updateProjectStatus"]
        assert update_project_status_2_resp is not None, "updateProjectStatus GraphQL response is None"

        # Firebase validation for Project.
        project_fb_id = update_processed_resp["result"]["firebaseId"]
        project_ref = self.firebase_helper.ref(Config.FirebaseKeys.project(project_fb_id))
        project_fb_data = project_ref.get()

        assert project_fb_data is not None, "Firebase data is None for Project"
        assert isinstance(project_fb_data, dict), "Firebase data is not a dictionary"
        assert project_fb_data["created"] is not None, "Created Date is empty"
        assert project_fb_data["projectId"] is not None, "ProjectId is empty"
        assert project_fb_data["tutorialId"] is not None, "TutorialId is empty"
        assert project_fb_data["projectId"] == project_fb_id, "projectId is not same as the firebaseId"
        tutorial.refresh_from_db()
        assert project_fb_data["tutorialId"] == tutorial.firebase_id, "tutorialId is not same as the firebaseId"
        assert datetime.fromisoformat(project_fb_data["created"]), "created is not a valid timestamp"

        # JSON comparison for project data with ignored keys.
        ignored_project_keys = {"created", "projectId", "tutorialId"}
        filtered_project_actual = remove_ignored_keys(project_fb_data, ignored_project_keys)
        filtered_project_expected = remove_ignored_keys(data["final_processed_project"], ignored_project_keys)
        assert filtered_project_actual == filtered_project_expected, "Difference found for project data in firebase."

        # Load group data to check if it is created correctly.
        project_group_ref = self.firebase_helper.ref(Config.FirebaseKeys.project_groups(project_fb_id))
        project_group_fb_data = project_group_ref.get()

        # JSON comparison for group data with ignored keys.
        ignored_group_keys = {"projectId"}
        filtered_group_actual = remove_ignored_keys(project_group_fb_data, ignored_group_keys)
        filtered_group_expected = remove_ignored_keys(data["final_group_data"], ignored_project_keys)
        assert filtered_group_actual == filtered_group_expected, "Difference found for group data in firebase"

        # Load task data to check if it is created correctly.
        project_tasks_ref = self.firebase_helper.ref(Config.FirebaseKeys.project_tasks(project_fb_id))
        project_task_fb_data_actual = project_tasks_ref.get()

        # JSON comparison for task data with ignored keys.
        ignored_task_keys = {"projectId", "url", "urlB"}
        sanitized_tasks_actual = remove_ignored_keys(project_task_fb_data_actual, ignored_task_keys)
        sanitized_tasks_expected = remove_ignored_keys(data["final_task_data"], ignored_task_keys)

        assert sanitized_tasks_actual == sanitized_tasks_expected, (
            "Differences found between expected and actual tasks in firebase."
        )

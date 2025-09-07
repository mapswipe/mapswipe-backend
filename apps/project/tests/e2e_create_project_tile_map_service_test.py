import typing
from datetime import datetime
from pathlib import Path

import json5
from django.conf import settings
from ulid import ULID

from apps.common.utils import remove_object_keys
from apps.contributor.factories import ContributorUserFactory
from apps.project.factories import OrganizationFactory
from apps.tutorial.factories import TutorialFactory
from apps.tutorial.models import Tutorial
from apps.user.factories import UserFactory
from main.config import Config
from main.tests import TestCase


class TestCompareProjectE2E(TestCase):
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
                firebaseId
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
                status
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

        cls.contributor_user = ContributorUserFactory.create(
            username="Ram Bahadur",
        )

        cls.user = UserFactory.create(
            contributor_user=cls.contributor_user,
        )
        cls.user_resource_kwargs = dict(
            created_by=cls.user,
            modified_by=cls.user,
        )

    def test_find_project_e2e(self):
        self._test_tile_map_service(
            "find",
            "assets/tests/projects/find/project_data.json5",
        )

    def test_completeness_project_e2e(self):
        self._test_tile_map_service(
            "completeness",
            "assets/tests/projects/completeness/project_data.json5",
        )

    def test_compare_project_e2e(self):
        self._test_tile_map_service(
            "compare",
            "assets/tests/projects/compare/project_data.json5",
        )

    def _test_tile_map_service(self, projectKey: str, filename: str):
        self.force_login(self.user)

        # Load test data file
        full_path = Path(settings.BASE_DIR, filename)
        with full_path.open("r", encoding="utf-8") as f:
            test_data = json5.load(f)

        # Define full path for image and AOI files
        image_filename = Path(settings.BASE_DIR) / test_data["assets"]["image"]
        aoi_geometry_filename = Path(settings.BASE_DIR) / test_data["assets"]["aoi"]

        # Load Project data initially.
        create_project_data = test_data["create_project"]

        # TODO: Use mutation to create organization
        # Create an organization and attach to project
        organization = OrganizationFactory.create(
            name=create_project_data["requestingOrganization"],
            **self.user_resource_kwargs,
        )
        create_project_data["requestingOrganization"] = organization.id

        # Create project
        with self.captureOnCommitCallbacks(execute=True):
            project_content = self.query_check(
                self.Mutation.CREATE_PROJECT,
                variables={"data": create_project_data},
            )

        project_response = project_content["data"]["createProject"]
        assert project_response is not None, "Project create response is None"
        assert project_response["ok"]

        project_id = project_response["result"]["id"]
        project_fb_id = project_response["result"]["firebaseId"]
        project_client_id = create_project_data["clientId"]

        # Create Image Asset for cover image
        image_asset_data = {
            "clientId": project_client_id,
            "inputType": "COVER_IMAGE",
            "project": project_id,
        }
        with image_filename.open("rb") as img_file:
            image_content = self.query_check(
                self.Mutation.UPLOAD_ASSET,
                variables={"data": image_asset_data},
                files={"imageFile": img_file},
                map={"imageFile": ["variables.data.file"]},
            )
        image_response = image_content["data"]["createProjectAsset"]
        assert image_response is not None, "Image create response is None"
        assert image_response["ok"]
        image_id = image_response["result"]["id"]

        # Create GeoJSON Asset for AOI Geometry
        aoi_asset_data = {
            "clientId": str(ULID()),
            "inputType": "AOI_GEOMETRY",
            "project": project_id,
        }
        with aoi_geometry_filename.open("rb") as geo_file:
            aoi_content = self.query_check(
                self.Mutation.UPLOAD_ASSET,
                variables={"data": aoi_asset_data},
                files={"geoFile": geo_file},
                map={"geoFile": ["variables.data.file"]},
            )
        aoi_response = aoi_content["data"]["createProjectAsset"]
        assert aoi_response is not None, "AOI create response is None"
        assert aoi_response["ok"]
        aoi_id = aoi_response["result"]["id"]

        # Update project
        update_project_data = test_data["update_project"]
        update_project_data["image"] = image_id
        update_project_data["projectTypeSpecifics"][projectKey]["aoiGeometry"] = aoi_id
        update_project_data["requestingOrganization"] = organization.id
        with self.captureOnCommitCallbacks(execute=True):
            update_content = self.query_check(
                self.Mutation.UPDATE_PROJECT,
                variables={"pk": project_id, "data": update_project_data},
            )
        update_response = update_content["data"]["updateProject"]
        assert update_response["ok"], update_response["errors"]
        assert update_response is not None, "Project update response is None"

        # Process project
        process_project_data = {
            "clientId": project_client_id,
            "status": "MARKED_AS_READY",
        }
        with self.captureOnCommitCallbacks(execute=True):
            process_project_content = self.query_check(
                self.Mutation.UPDATE_PROJECT_STATUS,
                variables={"pk": project_id, "data": process_project_data},
            )
        process_project_response = process_project_content["data"]["updateProjectStatus"]
        assert process_project_response is not None, "Project mark as ready response is None"
        assert process_project_response["ok"], process_project_response["errors"]
        assert process_project_response["result"]["status"] == "MARKED_AS_READY", "Project should be marked as ready"

        # TODO: Use mutation to create tutorial
        # Create tutorial to attach to project before publishing
        tutorial = TutorialFactory.create(
            **self.user_resource_kwargs,
            project_id=project_id,
            status=Tutorial.Status.PUBLISHED,
        )

        # Update processed project
        update_processed_project_data = test_data["update_processed_project"]
        update_processed_project_data["tutorial"] = tutorial.id
        update_processed_project_data["requestingOrganization"] = organization.id
        with self.captureOnCommitCallbacks(execute=True):
            update_processed_project_content = self.query_check(
                self.Mutation.UPDATE_PROCESSED_PROJECT,
                variables={"pk": project_id, "data": update_processed_project_data},
            )
        update_processed_response = update_processed_project_content["data"]["updateProcessedProject"]
        assert update_processed_response["ok"], update_processed_response["errors"]
        assert update_processed_response is not None, "Processed project update response is None"

        # Publish project
        publish_project_data = {
            "clientId": project_client_id,
            "status": "PUBLISHED",
        }
        with self.captureOnCommitCallbacks(execute=True):
            publish_project_content = self.query_check(
                self.Mutation.UPDATE_PROJECT_STATUS,
                variables={"pk": project_id, "data": publish_project_data},
            )
        publish_project_response = publish_project_content["data"]["updateProjectStatus"]
        assert publish_project_response["ok"], publish_project_response["errors"]
        assert publish_project_response is not None, "Processed project publish response is None"
        assert publish_project_response["result"]["status"] == "PUBLISHED", "Project should be published"

        # CHECK PROJECT, GROUP AND TASK CREATED IN FIREBASE

        project_fb_ref = self.firebase_helper.ref(f"/v2/projects/{project_fb_id}")
        project_fb_data = project_fb_ref.get()

        # Check project in firebase
        # tutorial.refresh_from_db()
        assert project_fb_data is not None, "Project in firebase is None"
        assert isinstance(project_fb_data, dict), "Project in firebase should be a dictionary"
        assert project_fb_data["created"] is not None, "Field 'created' should be defined"
        assert datetime.fromisoformat(project_fb_data["created"]), "Field 'created' should be a timestamp"
        assert project_fb_data["projectId"] == project_fb_id, "Field 'projectId' should match firebaseId"
        assert project_fb_data["tutorialId"] == tutorial.firebase_id, "Field 'tutorialId' should match tutorial's firebaseId"
        assert project_fb_data["createdBy"] == self.contributor_user.firebase_id, (
            "Field 'createdBy' should match contributor user's firebaseId"
        )

        ignored_project_keys = {"created", "createdBy", "projectId", "tutorialId"}
        filtered_project_actual = remove_object_keys(project_fb_data, ignored_project_keys)
        filtered_project_expected = remove_object_keys(test_data["expected_project_data"], ignored_project_keys)
        assert filtered_project_actual == filtered_project_expected, "Difference found for project data in firebase."

        # Check group in firebase
        groups_fb_ref = self.firebase_helper.ref(f"/v2/groups/{project_fb_id}/")
        groups_fb_data = groups_fb_ref.get()

        if groups_fb_data:
            for group in iter(groups_fb_data.values()):  # type: ignore[reportAttributeAccessIssue]
                assert group["projectId"] == project_fb_id, "Field 'projectId' of each group should match firebaseId"

        ignored_group_keys = {"projectId"}
        filtered_group_actual = remove_object_keys(groups_fb_data, ignored_group_keys)
        filtered_group_expected = remove_object_keys(test_data["expected_groups_data"], ignored_project_keys)
        assert filtered_group_actual == filtered_group_expected, "Difference found for group data in firebase."

        # Check group in firebase
        tasks_ref = self.firebase_helper.ref(Config.FirebaseKeys.project_tasks(project_fb_id))
        tasks_fb_data = tasks_ref.get()

        if tasks_fb_data:
            for groups in iter(tasks_fb_data.values()):  # type: ignore[reportAttributeAccessIssue]
                for task in groups:
                    assert task["projectId"] == project_fb_id, "Field 'projectId' of each task should match firebaseId"

        ignored_task_keys = {"projectId"}
        sanitized_tasks_actual = remove_object_keys(tasks_fb_data, ignored_task_keys)
        sanitized_tasks_expected = remove_object_keys(test_data["expected_tasks_data"], ignored_task_keys)

        assert sanitized_tasks_actual == sanitized_tasks_expected, (
            "Differences found between expected and actual tasks in firebase."
        )

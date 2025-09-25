import typing
from datetime import datetime
from pathlib import Path

import json5
from django.conf import settings
from ulid import ULID

from apps.common.utils import decode_tasks, remove_object_keys
from apps.contributor.factories import ContributorUserFactory
from apps.user.factories import UserFactory
from main.config import Config
from main.tests import TestCase


class TestStreetProjectE2E(TestCase):
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

        UPLOAD_PROJECT_ASSET = """
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

        CREATE_TUTORIAL = """
            mutation CreateTutorial($data: TutorialCreateInput!) {
              createTutorial(data: $data) {
                ... on OperationInfo {
                  __typename
                  messages {
                    code
                    field
                    kind
                    message
                  }
                }
                ... on TutorialTypeMutationResponseType {
                  errors
                  ok
                  result {
                    id
                    clientId
                    projectId
                    firebaseId
                  }
                }
              }
            }
        """

        UPDATE_TUTORIAL = """
            mutation UpdateTutorial($data: TutorialUpdateInput!, $pk: ID!) {
              updateTutorial(data: $data, pk: $pk) {
                ... on OperationInfo {
                  __typename
                  messages {
                    code
                    field
                    kind
                    message
                  }
                }
                ... on TutorialTypeMutationResponseType {
                  errors
                  ok
                  result {
                    id
                  }
                }
              }
            }
        """

        UPDATE_TUTORIAL_STATUS = """
            mutation UpdateTutorialStatus($data: TutorialStatusUpdateInput!, $pk: ID!) {
              updateTutorialStatus(data: $data, pk: $pk) {
                ... on OperationInfo {
                  __typename
                  messages {
                    code
                    field
                    kind
                    message
                  }
                }
                ... on TutorialTypeMutationResponseType {
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

    def test_street_project_e2e(self):
        self._test_project(
            "assets/tests/projects/street/project_data.json5",
        )

    # TODO(susilnem): Add more test with filters

    def _test_project(self, filename: str):
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

        # Create an organization and attach to project
        create_organization_data = test_data["create_organization"]
        with self.captureOnCommitCallbacks(execute=True):
            organization_content = self.query_check(
                self.Mutation.CREATE_ORGANIZATION,
                variables={"data": create_organization_data},
            )

        organization_response = organization_content["data"]["createOrganization"]
        assert organization_response is not None, "Organization create response is None"
        assert organization_response["ok"]

        organization_id = organization_response["result"]["id"]
        organization_fb_id = organization_response["result"]["firebaseId"]

        # CHECK ORGANIZATION in firebase

        organization_fb_ref = self.firebase_helper.ref(f"/v2/organisations/{organization_fb_id}")
        organization_fb_data = organization_fb_ref.get()

        # Check organization in firebase
        assert organization_fb_data is not None, "organization in firebase is None"
        assert isinstance(organization_fb_data, dict), "organization in firebase should be a dictionary"

        assert organization_fb_data == test_data["expected_organization_data"], (
            "Difference found for organization data in firebase."
        )

        # Create project
        create_project_data["requestingOrganization"] = organization_id
        with self.captureOnCommitCallbacks(execute=True):
            project_content = self.query_check(
                self.Mutation.CREATE_PROJECT,
                variables={"data": create_project_data},
            )

        project_response = project_content["data"]["createProject"]
        assert project_response is not None, "Project create response is None"
        assert project_response["ok"], project_response["errors"]

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
                self.Mutation.UPLOAD_PROJECT_ASSET,
                variables={"data": image_asset_data},
                files={"imageFile": img_file},
                map={"imageFile": ["variables.data.file"]},
            )
        image_response = image_content["data"]["createProjectAsset"]
        assert image_response is not None, "Image create response is None"
        assert image_response["ok"]
        image_id = image_response["result"]["id"]

        # Update project
        update_project_data = test_data["update_project"]
        update_project_data["requestingOrganization"] = organization_id
        update_project_data["image"] = image_id

        # Create GeoJSON Asset for AOI Geometry
        aoi_asset_data = {
            "clientId": str(ULID()),
            "inputType": "AOI_GEOMETRY",
            "project": project_id,
        }
        with aoi_geometry_filename.open("rb") as geo_file:
            aoi_content = self.query_check(
                self.Mutation.UPLOAD_PROJECT_ASSET,
                variables={"data": aoi_asset_data},
                files={"geoFile": geo_file},
                map={"geoFile": ["variables.data.file"]},
            )
        aoi_response = aoi_content["data"]["createProjectAsset"]
        assert aoi_response is not None, "AOI create response is None"
        assert aoi_response["ok"]
        aoi_id = aoi_response["result"]["id"]
        update_project_data["projectTypeSpecifics"]["street"]["aoiGeometry"] = aoi_id

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
            "status": "READY_TO_PROCESS",
        }
        with self.captureOnCommitCallbacks(execute=True):
            process_project_content = self.query_check(
                self.Mutation.UPDATE_PROJECT_STATUS,
                variables={"pk": project_id, "data": process_project_data},
            )
        process_project_response = process_project_content["data"]["updateProjectStatus"]
        assert process_project_response is not None, "Project ready to process response is None"
        assert process_project_response["ok"], process_project_response["errors"]
        assert process_project_response["result"]["status"] == "READY_TO_PROCESS", "Project should be ready to process"

        # Load Tutorial data initially.
        create_tutorial_data = test_data["create_tutorial"]
        create_tutorial_data["project"] = project_id
        with self.captureOnCommitCallbacks(execute=True):
            tutorial_content = self.query_check(
                self.Mutation.CREATE_TUTORIAL,
                variables={"data": create_tutorial_data},
            )

        tutorial_response = tutorial_content["data"]["createTutorial"]
        assert tutorial_response is not None, "Tutorial create response is None"
        assert tutorial_response["ok"]

        tutorial_id = tutorial_response["result"]["id"]
        tutorial_fb_id = tutorial_response["result"]["firebaseId"]
        tutorial_client_id = create_tutorial_data["clientId"]

        # Update Tutorial
        with self.captureOnCommitCallbacks(execute=True):
            update_tutorial_content = self.query_check(
                query=self.Mutation.UPDATE_TUTORIAL,
                variables={
                    "data": test_data["update_tutorial"],
                    "pk": tutorial_id,
                },
            )
        update_tutorial_response = update_tutorial_content["data"]["updateTutorial"]
        assert update_tutorial_response is not None, "Tutorial update response is None"
        assert update_tutorial_response["ok"], update_tutorial_response["errors"]
        assert update_tutorial_response is not None, "Tutorial update response is None"

        # Publish Tutorial
        publish_tutorial_data = {
            "clientId": tutorial_client_id,
            "status": "READY_TO_PUBLISH",
        }
        with self.captureOnCommitCallbacks(execute=True):
            publish_tutorial_content = self.query_check(
                self.Mutation.UPDATE_TUTORIAL_STATUS,
                variables={"pk": tutorial_id, "data": publish_tutorial_data},
            )
        publish_tutorial_response = publish_tutorial_content["data"]["updateTutorialStatus"]
        assert publish_tutorial_response["ok"], publish_tutorial_response["errors"]
        assert publish_tutorial_response is not None, "Processed tutorial publish response is None"
        assert publish_tutorial_response["result"]["status"] == "READY_TO_PUBLISH", "tutorial should be ready to published"

        # CHECK TUTORIAL, GROUP AND TASK CREATED IN FIREBASE

        tutorial_fb_ref = self.firebase_helper.ref(f"/v2/projects/{tutorial_fb_id}")
        tutorial_fb_data = tutorial_fb_ref.get()

        # Check tutorial in firebase
        assert tutorial_fb_data is not None, "Tutorial in firebase is None"
        assert isinstance(tutorial_fb_data, dict), "Tutorial in firebase should be a dictionary"
        assert tutorial_fb_data["projectId"] == tutorial_fb_id, "Field 'projectId' should match firebaseId"

        ignored_tutorial_keys = {"projectId", "tutorialDraftId"}
        filtered_tutorial_actual = remove_object_keys(tutorial_fb_data, ignored_tutorial_keys)
        filtered_tutorial_expected = remove_object_keys(test_data["expected_tutorial_data"], ignored_tutorial_keys)
        assert filtered_tutorial_actual == filtered_tutorial_expected, "Difference found for tutorial data in firebase."

        # Check group in firebase
        tutorial_groups_fb_ref = self.firebase_helper.ref(f"/v2/groups/{tutorial_fb_id}/")
        tutorial_groups_fb_data = tutorial_groups_fb_ref.get()

        if tutorial_groups_fb_data:
            for group in iter(tutorial_groups_fb_data.values()):  # type: ignore[reportAttributeAccessIssue]
                assert group["projectId"] == tutorial_fb_id, "Field 'tutorialId' of each group should match firebaseId"

        ignored_group_keys = {"projectId"}
        filtered_group_actual = remove_object_keys(tutorial_groups_fb_data, ignored_group_keys)
        filtered_group_expected = remove_object_keys(test_data["expected_tutorial_groups_data"], ignored_tutorial_keys)
        assert filtered_group_actual == filtered_group_expected, "Difference found for tutorial group data in firebase."

        # Check tutorial tasks in firebase
        tutorial_tasks_ref = self.firebase_helper.ref(f"/v2/tasks/{tutorial_fb_id}/")
        tutorial_task_fb_data = tutorial_tasks_ref.get()

        ignored_task_keys: set[str] = {"projectId"}
        sanitized_tutorial_tasks_actual: list[dict[str, typing.Any]] = []
        sanitized_tutorial_tasks_expected: list[dict[str, typing.Any]] = []

        for group in iter(tutorial_task_fb_data.values()):  # type: ignore[reportAttributeAccessIssue]
            for task_fb in decode_tasks(group):
                sanitized_tutorial_tasks_actual.append(remove_object_keys(task_fb, ignored_task_keys))  # type: ignore[reportGeneralTypeIssues]

        for group in iter(test_data["expected_tutorial_tasks_data"].values()):
            for task in decode_tasks(group):
                sanitized_tutorial_tasks_expected.append(remove_object_keys(task, ignored_task_keys))  # type: ignore[reportGeneralTypeIssues]

        # Sorting and comparing tasks
        sanitized_tasks_actual_sorted = sorted(sanitized_tutorial_tasks_actual, key=lambda t: t["taskId"])
        sanitized_tasks_expected_sorted = sorted(sanitized_tutorial_tasks_expected, key=lambda t: t["taskId"])

        assert sanitized_tasks_actual_sorted == sanitized_tasks_expected_sorted, (
            "Differences found between expected and actual tasks on tutorial in firebase."
        )

        # Update processed project
        update_processed_project_data = test_data["update_processed_project"]
        update_processed_project_data["tutorial"] = tutorial_id
        update_processed_project_data["requestingOrganization"] = organization_id
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
            "status": "READY_TO_PUBLISH",
        }
        with self.captureOnCommitCallbacks(execute=True):
            publish_project_content = self.query_check(
                self.Mutation.UPDATE_PROJECT_STATUS,
                variables={"pk": project_id, "data": publish_project_data},
            )
        publish_project_response = publish_project_content["data"]["updateProjectStatus"]
        assert publish_project_response["ok"], publish_project_response["errors"]
        assert publish_project_response is not None, "Processed project publish response is None"
        assert publish_project_response["result"]["status"] == "READY_TO_PUBLISH", "Project should be ready to published"

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
        assert project_fb_data["tutorialId"] == tutorial_fb_id, "Field 'tutorialId' should match tutorial's firebaseId"
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
        filtered_group_expected = remove_object_keys(test_data["expected_project_groups_data"], ignored_project_keys)
        assert filtered_group_actual == filtered_group_expected, "Difference found for group data on project in firebase."

        # Check tasks in firebase
        tasks_ref = self.firebase_helper.ref(Config.FirebaseKeys.project_tasks(project_fb_id))
        project_tasks_fb_data = tasks_ref.get()

        if project_tasks_fb_data:
            for groups in iter(project_tasks_fb_data.values()):  # type: ignore[reportAttributeAccessIssue]
                for task in groups:
                    assert task["projectId"] == project_fb_id, "Field 'projectId' of each task should match firebaseId"

        ignored_task_keys = {"projectId"}
        sanitized_tasks_actual = remove_object_keys(project_tasks_fb_data, ignored_task_keys)
        sanitized_tasks_expected = remove_object_keys(test_data["expected_project_tasks_data"], ignored_task_keys)

        assert sanitized_tasks_actual == sanitized_tasks_expected, (
            "Differences found between expected and actual tasks in firebase."
        )

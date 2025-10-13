import operator
import typing
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import json5
from django.db.models.signals import pre_save
from ulid import ULID

from apps.common.models import AssetTypeEnum
from apps.common.utils import remove_object_keys
from apps.contributor.factories import ContributorUserFactory
from apps.contributor.models import ContributorUserGroup
from apps.mapping.firebase.pull import pull_results_from_firebase
from apps.mapping.models import (
    MappingSession,
    MappingSessionResult,
    MappingSessionResultTemp,
    MappingSessionUserGroup,
    MappingSessionUserGroupTemp,
)
from apps.project.models import Organization, Project, ProjectAsset, ProjectAssetExportTypeEnum
from apps.project.tests.e2e_create_project_tile_map_service_test import read_csv, read_json
from apps.tutorial.models import Tutorial
from apps.user.factories import UserFactory
from main.config import Config
from main.tests import TestCase


@contextmanager
def create_override():
    def pre_save_override(sender: typing.Any, instance: typing.Any, **kwargs):  # type: ignore[reportMissingParameterType]
        if sender == Tutorial:
            instance.firebase_id = f"tutorial_{instance.client_id}"
        elif sender in {Project, Organization, ContributorUserGroup}:
            instance.firebase_id = instance.client_id

    pre_save.connect(pre_save_override)
    try:
        yield True
    finally:
        pre_save.disconnect(pre_save_override)


class TestValidateImageProjectE2E(TestCase):
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
                    status
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

        CREATE_CONTRIBUTOR_USER_GROUP = """
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
                        errors
                        ok
                        result {
                            id
                            name
                            description
                            clientId
                            isArchived
                            firebaseId
                        }
                    }
                }
            }
        """

    def test_validate_image_project_e2e(self):
        # TODO(susilnem): Add more test with filters
        with create_override():
            self._test_project(
                "assets/tests/projects/validate_image/project_data.json5",
            )

    # Generic functions

    def _test_project(self, filename: str):
        # Load test data file
        full_path = Path(Config.BASE_DIR, filename)
        with full_path.open("r", encoding="utf-8") as f:
            test_data = json5.load(f)

        # Create contributor user and login
        contributor_user = ContributorUserFactory.create(
            username="Ram Bahadur",
            firebase_id=test_data["contributor_user_firebase_id"],
        )
        user = UserFactory.create(
            contributor_user=contributor_user,
        )

        self.force_login(user)

        # Define full path for image and AOI files
        image_filename = Path(Config.BASE_DIR) / test_data["assets"]["image"]
        coco_filename = Path(Config.BASE_DIR) / test_data["assets"]["coco_dataset"]

        # Create an organization
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

        organization_fb_ref = self.firebase_helper.ref(f"/v2/organisations/{organization_fb_id}")
        organization_fb_data = organization_fb_ref.get()
        assert organization_fb_data is not None, "Organization in firebase is None"

        # Create project
        create_project_data = test_data["create_project"]
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

        # Create Image Asset for COCO images
        if test_data["update_project"]["projectTypeSpecifics"]["validateImage"]["sourceType"] == "DATASET_FILE":
            with coco_filename.open("r", encoding="utf-8") as f:
                coco_data = json5.load(f)
                for image in iter(coco_data["images"]):
                    image_asset_data = {
                        "clientId": str(ULID()),
                        "inputType": "OBJECT_IMAGE",
                        "project": project_id,
                        "assetTypeSpecifics": {
                            "objectImage": {
                                "image": {
                                    "cocoUrl": image["coco_url"],
                                    "fileName": image["file_name"],
                                    "height": image["height"],
                                    "id": str(image["id"]),
                                    "width": image["width"],
                                },
                            },
                        },
                        "externalUrl": image["coco_url"],
                    }
                    image_content = self.query_check(
                        self.Mutation.UPLOAD_PROJECT_ASSET,
                        variables={"data": image_asset_data},
                    )
                    image_response = image_content["data"]["createProjectAsset"]
                    assert image_response is not None, "image create response is None"
                    assert image_response["ok"]

        # Update project
        update_project_data = test_data["update_project"]
        update_project_data["image"] = image_id
        update_project_data["requestingOrganization"] = organization_id
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

        # Create tutorial from above project
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

        # Publish tutorial
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

        tutorial_fb_ref = self.firebase_helper.ref(f"/v2/projects/{tutorial_fb_id}")
        tutorial_fb_data = tutorial_fb_ref.get()

        # Check tutorial in firebase
        assert tutorial_fb_data is not None, "Tutorial in firebase is None"
        assert isinstance(tutorial_fb_data, dict), "Tutorial in firebase should be a dictionary"

        filtered_tutorial_actual = tutorial_fb_data
        filtered_tutorial_expected = test_data["expected_tutorial_data"]
        assert filtered_tutorial_actual == filtered_tutorial_expected, "Difference found for tutorial data in firebase."

        # Check tutorial groups in firebase
        tutorial_groups_fb_ref = self.firebase_helper.ref(f"/v2/groups/{tutorial_fb_id}/")
        tutorial_groups_fb_data = tutorial_groups_fb_ref.get()

        filtered_group_actual = tutorial_groups_fb_data
        filtered_group_expected = test_data["expected_tutorial_groups_data"]
        assert filtered_group_actual == filtered_group_expected, "Difference found for tutorial group data in firebase."

        # Check tutorial tasks in firebase
        tutorial_tasks_ref = self.firebase_helper.ref(f"/v2/tasks/{tutorial_fb_id}/")
        tutorial_task_fb_data = tutorial_tasks_ref.get()

        sanitized_tasks_actual = tutorial_task_fb_data
        sanitized_tasks_expected = test_data["expected_tutorial_tasks_data"]

        assert sanitized_tasks_actual == sanitized_tasks_expected, (
            "Differences found between expected and actual tasks on tutorial in firebase."
        )

        # Update processed project: attach tutorial, organization
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
        assert publish_project_response["result"]["status"] == "READY_TO_PUBLISH", "Project should be ready to publish"

        project_fb_ref = self.firebase_helper.ref(f"/v2/projects/{project_fb_id}")
        project_fb_data = project_fb_ref.get()

        # Check project in firebase
        assert project_fb_data is not None, "Project in firebase is None"
        assert isinstance(project_fb_data, dict), "Project in firebase should be a dictionary"
        assert project_fb_data["created"] is not None, "Field 'created' should be defined"
        assert datetime.fromisoformat(project_fb_data["created"]), "Field 'created' should be a timestamp"

        ignored_project_keys = {"created"}
        filtered_project_actual = remove_object_keys(project_fb_data, ignored_project_keys)
        filtered_project_expected = remove_object_keys(test_data["expected_project_data"], ignored_project_keys)
        assert filtered_project_actual == filtered_project_expected, "Difference found for project data in firebase."

        # Check project groups in firebase
        groups_fb_ref = self.firebase_helper.ref(f"/v2/groups/{project_fb_id}/")
        groups_fb_data = groups_fb_ref.get()

        filtered_group_actual = groups_fb_data
        filtered_group_expected = test_data["expected_project_groups_data"]
        assert filtered_group_actual == filtered_group_expected, "Difference found for group data on project in firebase."

        # Check project tasks in firebase
        project_tasks_ref = self.firebase_helper.ref(f"/v2/tasks/{project_fb_id}/")
        project_tasks_fb_data = project_tasks_ref.get()

        sanitized_tasks_actual = project_tasks_fb_data
        sanitized_tasks_expected = test_data["expected_project_tasks_data"]

        assert sanitized_tasks_actual == sanitized_tasks_expected, (
            "Differences found between expected and actual tasks on project in firebase."
        )

        # Create contributor user group
        old_contributor_user_group_data = test_data["create_contributor_user_group"]
        for input_data in old_contributor_user_group_data:
            usergroup_content = self.query_check(
                self.Mutation.CREATE_CONTRIBUTOR_USER_GROUP,
                variables={
                    "data": input_data,
                },
            )
            usergroup_response = usergroup_content["data"]["createContributorUserGroup"]
            assert usergroup_response is not None, "usergroup create response is None"
            assert usergroup_response["ok"]

        # Pull results from firebase
        input_data = test_data["create_results"]
        ref_results = self.firebase_helper.ref(f"/v2/results/{project_fb_id}")
        ref_results.set(input_data)

        fb_results_data = ref_results.get()
        assert fb_results_data is not None

        assert [
            MappingSession.objects.count(),
            MappingSessionResult.objects.count(),
            MappingSessionUserGroup.objects.count(),
            MappingSessionUserGroupTemp.objects.count(),
            MappingSessionResultTemp.objects.count(),
        ] == [0, 0, 0, 0, 0], "Mapping session data should be empty before pull from firebase"

        project = Project.objects.get(id=project_id)
        assert project.progress == 0

        with self.captureOnCommitCallbacks(execute=True):
            pull_results_from_firebase()

        assert [
            MappingSession.objects.count(),
            MappingSessionResult.objects.count(),
            MappingSessionUserGroup.objects.count(),
            MappingSessionUserGroupTemp.objects.count(),
            MappingSessionResultTemp.objects.count(),
        ] == [
            test_data["expected_pulled_results_data"]["mapping_session_count"],
            test_data["expected_pulled_results_data"]["mapping_session_results_count"],
            test_data["expected_pulled_results_data"]["mapping_session_user_groups_count"],
            0,
            0,
        ], "Difference found for pulled results data."

        project.refresh_from_db()
        assert project.progress == test_data["expected_pulled_results_data"]["progress"]

        # Check if progress and contributorCount synced to firebase
        project_fb_data = project_fb_ref.get()
        assert project_fb_data is not None, "Project in firebase is None"
        assert isinstance(project_fb_data, dict), "Project in firebase should be a dictionary"
        assert project_fb_data["progress"] == project.progress, "Progress should be synced with firebase"
        assert project_fb_data["contributorCount"] == 1, "Contributor count should be synced with firebase"

        if not test_data.get("expected_project_exports_data"):
            return

        # Check groups export
        groups_project_asset = ProjectAsset.objects.filter(
            project=project,
            type=AssetTypeEnum.EXPORT,
            export_type=ProjectAssetExportTypeEnum.GROUPS,
        ).first()
        assert groups_project_asset is not None, "Groups project asset not found"

        expected_groups = read_csv(
            Path(Config.BASE_DIR, test_data["expected_project_exports_data"]["groups"]),
            ignore_columns={
                "total_area",  # NOTE: previously empty, now real value
                "time_spent_max_allowed",  # NOTE: previously empty, now real value
            },
        )
        actual_groups = read_csv(
            groups_project_asset.file,
            compressed=True,
            ignore_columns={
                "total_area",  # NOTE: previously empty, now real value
                "time_spent_max_allowed",  # NOTE: previously empty, now real value
                "project_internal_id",  # NOTE: added for referencing
                "group_internal_id",  # NOTE: added for referencing
            },
        )
        assert expected_groups == actual_groups, "Difference found for groups export file."

        # Check tasks export
        tasks_project_asset = ProjectAsset.objects.filter(
            project=project,
            type=AssetTypeEnum.EXPORT,
            export_type=ProjectAssetExportTypeEnum.TASKS,
        ).first()
        assert tasks_project_asset is not None, "Tasks project asset not found"

        expected_tasks = read_csv(
            Path(Config.BASE_DIR, test_data["expected_project_exports_data"]["tasks"]),
            sort_column=operator.itemgetter("task_id"),
            ignore_columns={
                "",  # NOTE: dataframe index
            },
        )
        actual_tasks = read_csv(
            tasks_project_asset.file,
            compressed=True,
            sort_column=operator.itemgetter("task_id"),
            ignore_columns={
                "",  # NOTE: dataframe index
                "project_internal_id",  # NOTE: added for referencing
                "group_internal_id",  # NOTE: added for referencing
                "task_internal_id",  # NOTE: added for referencing
            },
        )
        assert expected_tasks == actual_tasks, "Difference found for tasks export file."

        # Check results export
        results_project_asset = ProjectAsset.objects.filter(
            project=project,
            type=AssetTypeEnum.EXPORT,
            export_type=ProjectAssetExportTypeEnum.RESULTS,
        ).first()
        assert results_project_asset is not None, "Results project asset not found"

        expected_results = read_csv(
            Path(Config.BASE_DIR, test_data["expected_project_exports_data"]["results"]),
            sort_column=operator.itemgetter("task_id"),
            ignore_columns={
                "",  # NOTE: dataframe index
            },
        )
        actual_results = read_csv(
            results_project_asset.file,
            sort_column=operator.itemgetter("task_id"),
            ignore_columns={
                "",  # NOTE: dataframe index
                "task_internal_id",  # NOTE: added for referencing
                "user_internal_id",  # NOTE: added for referencing
                "group_internal_id",  # NOTE: added for referencing
                "project_internal_id",  # NOTE: added for referencing
            },
            compressed=True,
        )
        assert expected_results == actual_results, "Difference found for results export file."

        # Check aggregated results export
        aggregated_results_project_asset = ProjectAsset.objects.filter(
            project=project,
            type=AssetTypeEnum.EXPORT,
            export_type=ProjectAssetExportTypeEnum.AGGREGATED_RESULTS,
        ).first()
        assert aggregated_results_project_asset is not None, "Aggregated results project asset not found"

        expected_aggregated_results = read_csv(
            Path(Config.BASE_DIR, test_data["expected_project_exports_data"]["aggregated_results"]),
        )
        actual_aggregated_results = read_csv(
            aggregated_results_project_asset.file,
            compressed=True,
            ignore_columns={
                "project_internal_id",  # NOTE: added for referencing
                "group_internal_id",  # NOTE: added for referencing
                "task_internal_id",  # NOTE: added for referencing
            },
        )

        assert expected_aggregated_results == actual_aggregated_results, (
            "Difference found for aggregated results export file."
        )

        # Check aggregated results with geometry export
        aggregated_results_with_geometry_project_asset = ProjectAsset.objects.filter(
            project=project,
            type=AssetTypeEnum.EXPORT,
            export_type=ProjectAssetExportTypeEnum.AGGREGATED_RESULTS_WITH_GEOMETRY,
        ).first()
        assert aggregated_results_with_geometry_project_asset is not None, (
            "Aggregated results with geometry project asset not found"
        )

        expected_aggregated_results_with_geometry = read_json(
            Path(Config.BASE_DIR, test_data["expected_project_exports_data"]["aggregated_results_with_geometry"]),
            ignore_fields={
                "name",  # NOTE: Previously "tmp", now "tmp" + random_str
            },
        )
        actual_aggregated_results_with_geometry = read_json(
            aggregated_results_with_geometry_project_asset.file,
            compressed=True,
            ignore_fields={
                "name",  # NOTE: Previously "tmp", now "tmp" + random_str
                "project_internal_id",  # NOTE: added for referencing
                "group_internal_id",  # NOTE: added for referencing
                "task_internal_id",  # NOTE: added for referencing
            },
        )
        assert expected_aggregated_results_with_geometry == actual_aggregated_results_with_geometry, (
            "Difference found for aggregated results with geometry export file."
        )

        # Check history export
        history_project_asset = ProjectAsset.objects.filter(
            project=project,
            type=AssetTypeEnum.EXPORT,
            export_type=ProjectAssetExportTypeEnum.HISTORY,
        ).first()
        assert history_project_asset is not None, "History project asset not found"

        expected_history = read_csv(
            Path(Config.BASE_DIR, test_data["expected_project_exports_data"]["history"]),
        )
        actual_history = read_csv(
            history_project_asset.file,
        )
        assert expected_history == actual_history, "Difference found for history export file."

        # Check users export
        users_project_asset = ProjectAsset.objects.filter(
            project=project,
            type=AssetTypeEnum.EXPORT,
            export_type=ProjectAssetExportTypeEnum.USERS,
        ).first()
        assert users_project_asset is not None, "Users project asset not found"

        expected_users = read_csv(
            Path(Config.BASE_DIR, test_data["expected_project_exports_data"]["users"]),
        )
        actual_users = read_csv(
            users_project_asset.file,
            compressed=True,
        )
        assert expected_users == actual_users, "Difference found for users export file."

import json
import typing
from pathlib import Path

from django.conf import settings
from ulid import ULID

from apps.project.factories import OrganizationFactory
from apps.project.models import Project
from apps.tutorial.factories import TutorialFactory
from apps.tutorial.models import Tutorial
from apps.user.factories import UserFactory
from main.config import Config
from main.tests import TestCase


class TestProjectE2E(TestCase):
    class Mutation:
        CREATE = """
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
                clientId
                projectType
                requestingOrganizationId
                requestingOrganization {
                  id
                  name
                }
                name
                topic
                region
                projectNumber
                lookFor
                additionalInfoUrl
                description
                verificationNumber
                groupSize
                maxTasksPerUser
                isFeatured
                status
                processingStatus
                progress
                tutorialId
                tutorial {
                  id
                }
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
                    clientId
                    projectType
                    requestingOrganizationId
                    requestingOrganization {
                      id
                      name
                    }
                    name
                    topic
                    region
                    projectNumber
                    lookFor
                    additionalInfoUrl
                    description
                    verificationNumber
                    groupSize
                    maxTasksPerUser
                    isFeatured
                    status
                    processingStatus
                    progress
                    tutorialId
                    tutorial {
                      id
                    }
                  }
                }
              }
            }
        """
        ASSET = """
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
                clientId
                type
                fileSize
                mimetype
                markedAsDeleted
                id
                projectId
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
                    clientId
                    projectType
                    requestingOrganizationId
                    requestingOrganization {
                    id
                    name
                    }
                    name
                    topic
                    region
                    projectNumber
                    lookFor
                    additionalInfoUrl
                    description
                    verificationNumber
                    groupSize
                    maxTasksPerUser
                    isFeatured
                    status
                    processingStatus
                    progress
                    tutorialId
                    tutorial {
                    id
                    }
                }
                }
            }
            }
        """

    @staticmethod
    def remove_ignored_keys(obj, keys_to_ignore):
        """
        Recursively remove keys from dicts if the key is in keys_to_ignore.
        Works on nested dicts and lists.
        """
        if isinstance(obj, dict):
            for key in list(obj.keys()):
                if key in keys_to_ignore:
                    obj.pop(key)
                else:
                    TestProjectE2E.remove_ignored_keys(obj[key], keys_to_ignore)
        elif isinstance(obj, list):
            for item in obj:
                TestProjectE2E.remove_ignored_keys(item, keys_to_ignore)
        return obj

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

        cls.organization = OrganizationFactory.create(**cls.user_resource_kwargs)

        cls.filename = Path(settings.BASE_DIR) / "test_data/project/create_find_project.json"
        cls.image_filename = Path(settings.BASE_DIR) / "apps/project/asset/image.jpg"
        cls.aoi_geometry_filename = Path(settings.BASE_DIR) / "apps/project/asset/find_geojson.geojson"

    def load_inputs(self) -> dict[str, typing.Any]:
        with self.filename.open("r", encoding="utf-8") as f:
            return json.load(f)

    def test_create_project(self):
        self.force_login(self.user)
        data = self.load_inputs()

        # Create Project data initially.
        create_project_data = data["create_project"]
        create_project_data["requestingOrganization"] = self.organization.id

        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(
                self.Mutation.CREATE,
                variables={"data": create_project_data},
            )

        resp = content["data"]["createProject"]
        assert resp is not None, "GraphQL response is None"
        result = resp["result"]

        assert {
            result["description"],
            result["lookFor"],
            result["projectType"],
        } == {
            create_project_data["description"],
            create_project_data["lookFor"],
            create_project_data["projectType"],
        }

        # Upload Image file.
        project = Project.objects.get(id=result["id"])
        image_asset_data = {
            "clientId": f"{create_project_data['clientId']}",
            "mimetype": "IMAGE_JPEG",
            "project": project.id,
        }

        with self.image_filename.open("rb") as img_file:
            image_resp = self.query_check(
                self.Mutation.ASSET,
                variables={"data": image_asset_data},
                files={
                    "imageFile": img_file,
                },
                map={
                    "imageFile": ["variables.data.file"],
                },
            )
        image_id = image_resp["data"]["createProjectAsset"]["result"]["id"]

        # Upload AOI geometry.
        aoi_asset_data = {
            "clientId": str(ULID()),
            "mimetype": "GEOJSON",
            "project": project.id,
        }

        with self.aoi_geometry_filename.open("rb") as geo_file:
            aoi_resp = self.query_check(
                self.Mutation.ASSET,
                variables={"data": aoi_asset_data},
                files={
                    "geoFile": geo_file,
                },
                map={
                    "geoFile": ["variables.data.file"],
                },
            )
        aoi_id = aoi_resp["data"]["createProjectAsset"]["result"]["id"]

        # Load update_project data and inject asset ids of image and AOI geometry.
        update_project_data = data["update_project"]
        update_project_data["image"] = image_id
        update_project_data["projectTypeSpecifics"]["find"]["aoiGeometry"] = aoi_id
        update_project_data["requestingOrganization"] = self.organization.id

        # Run the update mutation.
        with self.captureOnCommitCallbacks(execute=True):
            update_content = self.query_check(
                self.Mutation.UPDATE_PROJECT,
                variables={
                    "pk": project.id,
                    "data": update_project_data,
                },
            )

        update_resp = update_content["data"]["updateProject"]
        assert update_resp is not None, "UpdateProject GraphQL response is None"
        update_result = update_resp["result"]

        # Compare key fields after update.
        assert {
            update_result["lookFor"],
            update_result["status"],
        } == {
            update_project_data["lookFor"],
            update_project_data["status"],
        }

        # Use factory for tutorial creation.
        tutorial = TutorialFactory.create(
            **self.user_resource_kwargs,
            project=project,
            status=Tutorial.Status.PUBLISHED,
        )

        # Load update_processed_project data.
        update_processed_project_data = data["update_processed_project"]
        update_processed_project_data["tutorial"] = tutorial.id
        update_processed_project_data["requestingOrganization"] = self.organization.id

        # Run the update_processed_project mutation.
        with self.captureOnCommitCallbacks(execute=True):
            update_processed_content = self.query_check(
                self.Mutation.UPDATE_PROCESSED_PROJECT,
                variables={
                    "pk": project.id,
                    "data": update_processed_project_data,
                },
            )

        update_processed_resp = update_processed_content["data"]["updateProcessedProject"]
        assert update_processed_resp is not None, "UpdateProcessedProject GraphQL response is None"
        update_processed_result = update_processed_resp["result"]

        # Compare key fields after processed update.
        assert {
            update_processed_result["status"],
            update_processed_result["lookFor"],
        } == {
            update_processed_project_data["status"],
            update_processed_project_data["lookFor"],
        }

        # Comparing project name.
        processed_project = Project.objects.get(id=update_processed_result["id"])
        assert update_processed_result["name"] == processed_project.generate_name()

        # Firebase validation for Project.
        project_fb_id = Project.objects.get(id=result["id"]).firebase_id
        project_ref = self.firebase_helper.ref(
            Config.FirebaseKeys.project(project_fb_id),
        )
        project_fb_data = project_ref.get()

        assert project_fb_data is not None, "Firebase data is None for Project"
        assert isinstance(project_fb_data, dict), "Firebase data is not a dictionary"

        # JSON comparison for project data with ignored keys.
        ignored_project_keys = {
            "created",
            "projectId",
            "tutorialId",
        }

        filtered_project_actual = self.remove_ignored_keys(project_fb_data, ignored_project_keys)
        filtered_project_expected = self.remove_ignored_keys(data["final_processed_project"], ignored_project_keys)

        assert filtered_project_actual == filtered_project_expected, (
            "Differences found when comparing Firebase data to fixed file create_find_project.json for project data."
        )

        # Load group data to check if it is created correctly.
        project_group_ref = self.firebase_helper.ref(
            Config.FirebaseKeys.project_groups(project_fb_id),
        )
        project_group_fb_data = project_group_ref.get()

        # JSON comparison for group data with ignored keys.
        ignored_group_keys = {
            "projectId",
        }

        filtered_group_actual = self.remove_ignored_keys(project_group_fb_data, ignored_group_keys)
        filtered_group_expected = self.remove_ignored_keys(data["final_group_data"], ignored_project_keys)

        assert filtered_group_actual == filtered_group_expected, (
            "Differences found when comparing Firebase data to fixed file create_find_project.json for group."
        )

        # Load task data to check if it is created correctly.
        project_tasks_ref = self.firebase_helper.ref(
            Config.FirebaseKeys.project_tasks(project_fb_id),
        )
        project_task_fb_data = project_tasks_ref.get()

        # Since the task data is not stored in firebase it should be None.
        assert project_task_fb_data is None

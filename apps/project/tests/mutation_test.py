import typing
from io import BytesIO
from pathlib import Path
from unittest.mock import call, patch

from django.conf import settings
from django.core.files.temp import NamedTemporaryFile
from PIL import Image
from ulid import ULID

from apps.common.models import IconEnum
from apps.contributor.factories import ContributorTeamFactory
from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.project.models import (
    Organization,
    Project,
    ProjectAssetInputTypeEnum,
    ProjectStatusEnum,
    ProjectTask,
    ProjectTaskGroup,
    ProjectTypeEnum,
)
from apps.project.tasks import process_project_task
from apps.tutorial.factories import TutorialFactory
from apps.tutorial.models import Tutorial
from apps.user.factories import UserFactory
from main.config import Config
from main.tests import TestCase
from project_types.street import project as street_project
from project_types.tile_map_service.compare import project as compare_project
from utils.geo.raster_tile_server.config import RasterTileServerNameEnum

BASE_DIR = Path(__file__).resolve().parent


def create_project_image_asset_query(
    *,
    query_check_func: typing.Callable,
    query: str,
    project_asset_data: dict,
    **kwargs,
) -> dict:
    with (
        NamedTemporaryFile(dir=settings.TEMP_DIR, suffix=".jpeg") as image_file,
    ):
        img = Image.new("RGB", (10, 10), color="red")
        buf = BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        image_file.write(buf.read())
        image_file.seek(0)

        return query_check_func(
            query,
            variables={
                "data": project_asset_data,
            },
            files={
                "imageFile": image_file,
            },
            map={
                "imageFile": ["variables.data.file"],
            },
            **kwargs,
        )


def create_project_aoi_asset_query(
    *,
    query_check_func: typing.Callable,
    query: str,
    project_asset_data: dict,
    **kwargs,
) -> dict:
    with (
        Path(BASE_DIR / "data/ring-road.geojson").open(encoding="utf-8") as geo_file,
    ):
        return query_check_func(
            query,
            variables={
                "data": project_asset_data,
            },
            files={
                "geoFile": geo_file,
            },
            map={
                "geoFile": ["variables.data.file"],
            },
            **kwargs,
        )


def update_project_query(
    *,
    query_check_func: typing.Callable,
    query: str,
    pk: str,
    project_data: dict,
    **kwargs,
) -> dict:
    return query_check_func(
        query,
        variables={
            "pk": pk,
            "data": project_data,
        },
        **kwargs,
    )


class Mutation:
    CREATE_PROJECT_ASSET = """
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
                clientId
                type
                mimetype
                projectId
                assetTypeSpecifics {
                  ... on AoiGeometryAssetPropertyType {
                    __typename
                    area
                    bbox
                    center
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
                projectInstruction
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
                projectInstruction
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
                aoiGeometryInputAsset {
                  id
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
                projectInstruction
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


class TestOrganizationMutation(TestCase):
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
                    errors
                    ok
                    result {
                        id
                        name
                        clientId
                        description
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
                    errors
                    ok
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
        cls.user_resource_kwargs = dict(
            created_by=cls.user,
            modified_by=cls.user,
        )

    def test_organization(self):
        organization_data = {
            "clientId": str(ULID()),
            "name": "Test Organization",
            "description": "Test description",
            "abbreviation": "TO",
        }

        # Creating Organization: Without authentication
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(
                self.Mutation.CREATE_ORGANIZATION,
                variables={
                    "data": organization_data,
                },
            )
        assert content["data"]["createOrganization"]["messages"] == [
            {
                "code": None,
                "field": "createOrganization",
                "kind": "PERMISSION",
                "message": "User is not authenticated.",
            },
        ], content

        # Creating Organization: With authentication
        self.force_login(self.user)
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(
                self.Mutation.CREATE_ORGANIZATION,
                variables={
                    "data": organization_data,
                },
            )
        resp_data = content["data"]["createOrganization"]
        assert resp_data["errors"] is None, content

        organization = Organization.objects.get(id=resp_data["result"]["id"])
        ref = self.firebase_helper.ref(Config.FirebaseKeys.organization(organization.firebase_id))
        fb_organization: typing.Any = ref.get()
        assert fb_organization is not None

        # Updating Organization
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(
                self.Mutation.UPDATE_ORGANIZATION,
                variables={
                    "data": {
                        "name": "Org Updated",
                        "clientId": resp_data["result"]["clientId"],
                        "description": "Update description",
                        "abbreviation": "OU",
                    },
                    "pk": resp_data["result"]["id"],
                },
            )
        resp_data = content["data"]["updateOrganization"]
        assert resp_data["errors"] is None, content
        fb_organization = ref.get()
        assert fb_organization is not None
        assert fb_organization.get("name") == "Org Updated"

        # Archive Organization
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(
                self.Mutation.UPDATE_ORGANIZATION,
                variables={
                    "data": {
                        "name": "Archive Org",
                        "clientId": resp_data["result"]["clientId"],
                        "description": "Update description",
                        "abbreviation": "AO",
                        "isArchived": True,
                    },
                    "pk": resp_data["result"]["id"],
                },
            )
        resp_data = content["data"]["updateOrganization"]
        assert resp_data["errors"] is None, content
        assert resp_data["result"]["isArchived"]
        assert resp_data["result"]["description"] == "Update description"
        assert resp_data["result"]["abbreviation"] == "AO"

        fb_organization = ref.get()
        assert fb_organization.get("isArchived")


class TestProjectMutation(TestCase):
    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory.create()
        cls.user_resource_kwargs = dict(
            created_by=cls.user,
            modified_by=cls.user,
        )

        cls.organization = OrganizationFactory.create(**cls.user_resource_kwargs)

    def _create_project_aoi_asset(self, project_asset_data: dict, **kwargs):
        with self.captureOnCommitCallbacks(execute=True):
            return create_project_aoi_asset_query(
                query_check_func=self.query_check,
                query=Mutation.CREATE_PROJECT_ASSET,
                project_asset_data={
                    **project_asset_data,
                    "inputType": self.genum(ProjectAssetInputTypeEnum.AOI_GEOMETRY),
                },
            )

    def _create_project_image_asset(self, project_asset_data: dict, **kwargs):
        with self.captureOnCommitCallbacks(execute=True):
            return create_project_image_asset_query(
                query_check_func=self.query_check,
                query=Mutation.CREATE_PROJECT_ASSET,
                project_asset_data={
                    **project_asset_data,
                    "inputType": self.genum(ProjectAssetInputTypeEnum.COVER_IMAGE),
                },
            )

    def _create_project_mutation(self, project_data: dict, **kwargs):
        with self.captureOnCommitCallbacks(execute=True):
            return self.query_check(
                query=Mutation.CREATE_PROJECT,
                variables={
                    "data": project_data,
                },
            )

    def _update_project_mutation(self, pk: str, project_data: dict, **kwargs):
        with self.captureOnCommitCallbacks(execute=True):
            return update_project_query(
                query_check_func=self.query_check,
                query=Mutation.UPDATE_PROJECT,
                pk=pk,
                project_data=project_data,
                **kwargs,
            )

    def _update_processed_project_mutation(self, pk: str, project_data: dict, **kwargs):
        with self.captureOnCommitCallbacks(execute=True):
            return update_project_query(
                query_check_func=self.query_check,
                query=Mutation.UPDATE_PROCESSED_PROJECT,
                pk=pk,
                project_data=project_data,
                **kwargs,
            )

    def _update_project_status_mutation(self, pk: str, project_data: dict, **kwargs):
        with self.captureOnCommitCallbacks(execute=True):
            return update_project_query(
                query_check_func=self.query_check,
                query=Mutation.UPDATE_PROJECT_STATUS,
                pk=pk,
                project_data=project_data,
                **kwargs,
            )

    def test_project_create(self):
        project_data = {
            "clientId": str(ULID()),
            "projectType": self.genum(ProjectTypeEnum.FIND),
            "topic": "New Project 101",
            "region": "Test Region",
            "projectNumber": 1,
            "requestingOrganization": self.organization.pk,
            "projectInstruction": "Buildings",
            "additionalInfoUrl": "https://hi-there/about.html",
            "description": "The new **project** from hi-there.",
        }

        # Creating Project: Without authentication
        content = self._create_project_mutation(project_data)
        assert content["data"]["createProject"]["messages"] == [
            {
                "code": None,
                "field": "createProject",
                "kind": "PERMISSION",
                "message": "User is not authenticated.",
            },
        ], content

        # Creating Project: With Authentication
        self.force_login(self.user)
        content = self._create_project_mutation(project_data)
        resp_data = content["data"]["createProject"]
        assert resp_data["errors"] is None, content

        # TODO: Do we add a validation for unique project name?

        # Creating project with archived team
        # Fails as team is archived
        archived_team = ContributorTeamFactory.create(
            **self.user_resource_kwargs,
            is_archived=True,
        )
        project_data["clientId"] = str(ULID())
        project_data["team"] = archived_team.pk
        project_data["topic"] = "Another Project 101"
        content = self._create_project_mutation(project_data)
        response = content["data"]["createProject"]
        assert response["errors"] == [
            {
                "array_errors": None,
                "client_id": project_data["clientId"],
                "field": "team",
                "messages": "Cannot use archived team on a project.",
                "object_errors": None,
                "pydantic_errors": None,
            },
        ], content

        latest_project = Project.objects.get(pk=resp_data["result"]["id"])
        assert latest_project.created_by_id == self.user.pk
        assert latest_project.modified_by_id == self.user.pk
        assert resp_data == self.g_mutation_response(
            ok=True,
            result=dict(
                id=self.gID(latest_project.pk),
                clientId=latest_project.client_id,
                projectType=self.genum(ProjectTypeEnum.FIND),
                requestingOrganizationId=self.gID(latest_project.requesting_organization.pk),
                requestingOrganization=dict(
                    id=self.gID(latest_project.requesting_organization.pk),
                    name=latest_project.requesting_organization.name,
                ),
                name=f"{latest_project.project_type_enum.label} {latest_project.topic} - {latest_project.region} ({latest_project.project_number}) {latest_project.requesting_organization.name}",  # noqa: E501
                topic=latest_project.topic,
                region=latest_project.region,
                projectNumber=latest_project.project_number,
                projectInstruction=latest_project.project_instruction,
                lookFor=None,
                additionalInfoUrl=latest_project.additional_info_url,
                description=latest_project.description,
                verificationNumber=3,
                groupSize=10,
                maxTasksPerUser=10,
                isFeatured=latest_project.is_featured,
                status=self.genum(Project.Status.DRAFT),
                processingStatus=None,
                progress=0,
                tutorialId=None,
                tutorial=None,
            ),
        ), content

        # Creating project with archived organization
        # Fails as organization is archived
        archived_organization = OrganizationFactory.create(
            **self.user_resource_kwargs,
            is_archived=True,
        )
        new_project_client_id = str(ULID())
        project_data["clientId"] = new_project_client_id
        project_data["requestingOrganization"] = archived_organization.pk
        content = self._create_project_mutation(project_data)
        assert content["data"]["createProject"]["errors"] == [
            {
                "array_errors": None,
                "client_id": new_project_client_id,
                "field": "requestingOrganization",
                "messages": "Cannot use archived organization on a project.",
                "object_errors": None,
                "pydantic_errors": None,
            },
            {
                "array_errors": None,
                "client_id": new_project_client_id,
                "field": "team",
                "messages": "Cannot use archived team on a project.",
                "object_errors": None,
                "pydantic_errors": None,
            },
        ], content

    @patch("apps.project.serializers.process_project_task.delay")
    def test_project_update(self, mock_requests):
        proj = ProjectFactory.create(
            **self.user_resource_kwargs,
            project_type=ProjectTypeEnum.FIND,
            topic="Test Project",
            region="Test Region",
            project_number=1,
            requesting_organization=self.organization,
            project_instruction="Buildings",
            additional_info_url="https://hi-there/about.html",
            description="The new **project** from hi-there.",
            project_type_specifics={},
        )

        project_data = {
            "requestingOrganization": self.organization.pk,
            "projectInstruction": "Buildings and Houses",
            "additionalInfoUrl": "https://hi-there/about.html?code=1",
            "description": "The new updated **project** from hi-there.",
            "verificationNumber": 2,
            "groupSize": 16,
            "maxTasksPerUser": 11,
            "clientId": proj.client_id,
        }

        # Updating Project: Without authentication
        content = self._update_project_mutation(str(proj.pk), project_data)
        assert content["data"]["updateProject"]["messages"] == [
            {
                "code": None,
                "field": "updateProject",
                "kind": "PERMISSION",
                "message": "User is not authenticated.",
            },
        ], content

        # Updating Project: With authentication
        self.force_login(self.user)
        content = self._update_project_mutation(str(proj.pk), project_data)
        resp_data = content["data"]["updateProject"]
        assert resp_data["errors"] is None, content

        latest_project = Project.objects.get(pk=proj.pk)
        assert resp_data == self.g_mutation_response(
            ok=True,
            result=dict(
                id=self.gID(latest_project.pk),
                clientId=latest_project.client_id,
                projectType=self.genum(ProjectTypeEnum.FIND),
                requestingOrganizationId=self.gID(latest_project.requesting_organization.pk),
                aoiGeometryInputAsset=None,
                requestingOrganization=dict(
                    id=self.gID(latest_project.requesting_organization.pk),
                    name=latest_project.requesting_organization.name,
                ),
                name=f"{latest_project.project_type_enum.label} {latest_project.topic} - {latest_project.region} ({latest_project.project_number}) {latest_project.requesting_organization.name}",  # noqa: E501
                topic=latest_project.topic,
                region=latest_project.region,
                projectNumber=latest_project.project_number,
                projectInstruction=latest_project.project_instruction,
                lookFor=None,
                additionalInfoUrl=latest_project.additional_info_url,
                description=latest_project.description,
                verificationNumber=latest_project.verification_number,
                groupSize=latest_project.group_size,
                maxTasksPerUser=latest_project.max_tasks_per_user,
                isFeatured=latest_project.is_featured,
                status=self.genum(Project.Status.DRAFT),
                processingStatus=None,
                progress=0,
                tutorialId=None,
                tutorial=None,
            ),
        ), content

        # Updating project with archived team
        # fails as team is archived
        archived_team = ContributorTeamFactory.create(
            **self.user_resource_kwargs,
            is_archived=True,
        )
        project_data["team"] = archived_team.pk
        content = self._update_project_mutation(str(latest_project.pk), project_data)
        assert content["data"]["updateProject"]["errors"] == [
            {
                "array_errors": None,
                "client_id": latest_project.client_id,
                "field": "team",
                "messages": "Cannot use archived team on a project.",
                "object_errors": None,
                "pydantic_errors": None,
            },
        ], content

        # Updating project with archived organization
        # Fails as organization is archived
        archived_organization = OrganizationFactory.create(
            **self.user_resource_kwargs,
            is_archived=True,
        )
        project_data["requestingOrganization"] = archived_organization.pk
        content = self._update_project_mutation(str(latest_project.pk), project_data)
        assert content["data"]["updateProject"]["errors"] == [
            {
                "array_errors": None,
                "client_id": latest_project.client_id,
                "field": "requestingOrganization",
                "messages": "Cannot use archived organization on a project.",
                "object_errors": None,
                "pydantic_errors": None,
            },
            {
                "array_errors": None,
                "client_id": latest_project.client_id,
                "field": "team",
                "messages": "Cannot use archived team on a project.",
                "object_errors": None,
                "pydantic_errors": None,
            },
        ], content

        # Updating Project: Status change
        # fails as project specifics is required when changing status to "ready to process"
        project_data = {
            "clientId": proj.client_id,
            "status": self.genum(Project.Status.READY_TO_PROCESS),
        }
        content = self._update_project_status_mutation(str(latest_project.pk), project_data)
        assert content["data"]["updateProjectStatus"]["errors"] == [
            {
                "array_errors": None,
                "client_id": latest_project.client_id,
                "field": "projectTypeSpecifics",
                "messages": "project_type_specifics is required when project status is Ready to Process",
                "object_errors": None,
                "pydantic_errors": None,
            },
        ]

        # Creating AOI Project Asset
        project_asset_data = {
            "clientId": str(ULID()),
            "project": str(latest_project.pk),
        }
        content = self._create_project_aoi_asset(project_asset_data)
        resp_data = content["data"]["createProjectAsset"]
        assert resp_data["errors"] is None, content
        aoi_geometry_asset = resp_data["result"]

        assert aoi_geometry_asset["assetTypeSpecifics"]["area"] == 42.995920243640064
        assert aoi_geometry_asset["assetTypeSpecifics"]["center"] == [85.31965030726025, 27.701474012628434]
        assert aoi_geometry_asset["assetTypeSpecifics"]["bbox"] == [
            85.28138075927546,
            27.65808616735157,
            85.35521103605072,
            27.742487621391874,
        ]

        # Creating Project Image Asset
        project_asset_data = {
            "clientId": str(ULID()),
            "project": str(latest_project.pk),
        }
        content = self._create_project_image_asset(project_asset_data)
        resp_data = content["data"]["createProjectAsset"]
        assert resp_data["errors"] is None, content
        image_asset = resp_data["result"]

        # Updating Project: with empty object as project type specifics
        # project_data = {
        #     "clientId": proj.client_id,
        #     "projectTypeSpecifics": {},
        # }
        # content = self._update_project_mutation(str(latest_project.pk), project_data, assert_errors=True)
        # assert content["errors"] == [
        #     {
        #         "message": "OneOf Input Object 'ProjectTypeSpecificInput' must specify exactly one key.",
        #     },
        # ]

        # Updating Project: with valid but mismatching project type specifics
        project_data = {
            "clientId": proj.client_id,
            "image": image_asset["id"],
            "projectTypeSpecifics": {
                "compare": {
                    "aoiGeometry": aoi_geometry_asset["id"],
                    "zoomLevel": 15,
                    "tileServerProperty": {
                        "name": self.genum(RasterTileServerNameEnum.CUSTOM),
                        "custom": {
                            "url": "https://hi-there/{x}/{y}/{z}",
                            "credits": "My Map",
                        },
                    },
                    "tileServerBProperty": {
                        "name": self.genum(RasterTileServerNameEnum.CUSTOM),
                        "custom": {
                            "url": "https://hi-there-2/{x}/{y}/{z}",
                            "credits": "My Map 2",
                        },
                    },
                },
            },
        }
        content = self._update_project_mutation(str(latest_project.pk), project_data)
        assert content["data"]["updateProject"]["errors"] == [
            {
                "field": "projectTypeSpecifics",
                "client_id": latest_project.client_id,
                "messages": "Configuration not provided for Find",
                "object_errors": None,
                "array_errors": None,
                "pydantic_errors": None,
            },
        ]

        # Updating Project: with valid project type specifics
        project_data = {
            "clientId": proj.client_id,
            "image": image_asset["id"],
            "projectTypeSpecifics": {
                "find": {
                    "aoiGeometry": aoi_geometry_asset["id"],
                    "zoomLevel": 15,
                    "tileServerProperty": {
                        "name": self.genum(RasterTileServerNameEnum.CUSTOM),
                        "custom": {
                            "url": "https://hi-there/{x}/{y}/{z}",
                            "credits": "My Map",
                        },
                    },
                },
            },
        }

        content = self._update_project_mutation(str(latest_project.pk), project_data)
        resp_data = content["data"]["updateProject"]
        assert resp_data["errors"] is None, content

        latest_project.refresh_from_db()
        assert latest_project.image_id == int(image_asset["id"])
        assert latest_project.aoi_geometry_input_asset
        assert latest_project.aoi_geometry_input_asset.id == int(aoi_geometry_asset["id"])
        assert latest_project.project_type_specifics == {
            "zoom_level": 15,
            "aoi_geometry": aoi_geometry_asset["id"],
            "tile_server_property": {
                "name": RasterTileServerNameEnum.CUSTOM.value,
                "custom": {
                    "credits": "My Map",
                    "url": "https://hi-there/{x}/{y}/{z}",
                },
            },
        }

        # Updating Project: Status change
        project_data = {
            "clientId": proj.client_id,
            "status": self.genum(Project.Status.READY_TO_PROCESS),
        }
        content = self._update_project_status_mutation(str(latest_project.pk), project_data)
        assert content["data"]["updateProjectStatus"]["errors"] is None

        mock_requests.assert_called_once()
        mock_requests.assert_has_calls([call(latest_project.pk)])

        process_project_task(latest_project.pk)

        latest_project.refresh_from_db()

        assert latest_project.status == Project.Status.PROCESSED

        # Updating processed project with archived Organization
        # Fails as organization is archived
        archived_organization = OrganizationFactory.create(
            **self.user_resource_kwargs,
            is_archived=True,
        )
        project_data = {
            "clientId": proj.client_id,
            "requestingOrganization": archived_organization.pk,
        }
        content = self._update_processed_project_mutation(str(latest_project.pk), project_data)
        assert content["data"]["updateProcessedProject"]["errors"] == [
            {
                "array_errors": None,
                "client_id": proj.client_id,
                "field": "requestingOrganization",
                "messages": "Cannot use archived organization on a project.",
                "object_errors": None,
                "pydantic_errors": None,
            },
        ], content

        # Attaching Tutorial to Project
        # fails as tutorial is archived
        archived_tutorial = TutorialFactory.create(
            **self.user_resource_kwargs,
            project=latest_project,
            status=Tutorial.Status.ARCHIVED,
        )

        project_data = {
            "clientId": proj.client_id,
            "tutorial": self.gID(archived_tutorial.pk),
        }
        content = self._update_project_mutation(str(latest_project.pk), project_data)
        assert content["data"]["updateProject"]["errors"] == [
            {
                "array_errors": None,
                "client_id": proj.client_id,
                "field": "tutorial",
                "messages": "Cannot use archived tutorial on a project.",
                "object_errors": None,
                "pydantic_errors": None,
            },
        ], content

        # Publish a project
        # set unarchived tutorial to project before publishing a project
        tutorial = TutorialFactory.create(
            **self.user_resource_kwargs,
            project=latest_project,
            status=Tutorial.Status.PUBLISHED,
        )
        project_data = {
            "clientId": proj.client_id,
            "tutorial": tutorial.id,
        }
        content = self._update_processed_project_mutation(str(latest_project.pk), project_data)
        assert content["data"]["updateProcessedProject"]["errors"] is None, content
        latest_project.refresh_from_db()

        project_data = {
            "clientId": proj.client_id,
            "status": self.genum(Project.Status.READY_TO_PUBLISH),
        }
        content = self._update_project_status_mutation(str(latest_project.pk), project_data)
        assert content["data"]["updateProjectStatus"]["errors"] is None
        latest_project.refresh_from_db()

        project_ref = self.firebase_helper.ref(
            Config.FirebaseKeys.project(latest_project.firebase_id),
        )
        fb_project: typing.Any = project_ref.get()
        assert fb_project is not None

        # Archiving tutorial
        # TODO: Add a test by archiving tutorial used in a published project

        # Withdraw processed project
        project_data = {
            "clientId": proj.client_id,
            "status": self.genum(ProjectStatusEnum.WITHDRAWN),
        }
        content = self._update_project_status_mutation(str(latest_project.pk), project_data)
        assert content["data"]["updateProjectStatus"]["errors"] is None, content
        assert content["data"]["updateProjectStatus"]["result"]["status"] == self.genum(ProjectStatusEnum.WITHDRAWN)

        # Updating project with archived team
        # fails as team is archived
        archived_team = ContributorTeamFactory.create(
            **self.user_resource_kwargs,
            is_archived=True,
        )
        project_data = {
            "clientId": proj.client_id,
            "team": archived_team.pk,
        }
        content = self._update_processed_project_mutation(str(latest_project.pk), project_data)
        assert content["data"]["updateProcessedProject"]["errors"] == [
            {
                "array_errors": None,
                "client_id": proj.client_id,
                "field": "team",
                "messages": "Cannot use archived team on a project.",
                "object_errors": None,
                "pydantic_errors": None,
            },
        ], content


class TestProjectTypeMutation(TestCase):
    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory.create()
        cls.user_resource_kwargs = dict(
            created_by=cls.user,
            modified_by=cls.user,
        )

        cls.organization = OrganizationFactory.create(**cls.user_resource_kwargs)

        cls.compare_project = ProjectFactory.create(
            **cls.user_resource_kwargs,
            project_type=ProjectTypeEnum.COMPARE,
            requesting_organization=cls.organization,
            project_type_specifics=None,
        )
        cls.compare_tutorial = TutorialFactory.create(
            **cls.user_resource_kwargs,
            project=cls.compare_project,
        )

        cls.project_data = {
            "topic": "Test Project",
            "region": "Test Region",
            "projectNumber": 1,
            "requestingOrganization": cls.organization.pk,
            "projectInstruction": "Buildings",
        }

        cls.tile_server_property = {
            "valid_custom": {
                "name": cls.genum(RasterTileServerNameEnum.CUSTOM),
                "custom": {
                    "url": "https://hi-there/{x}/{y}/{z}",
                    "credits": "My Map",
                },
            },
            "valid_custom_02": {
                "name": cls.genum(RasterTileServerNameEnum.CUSTOM),
                "custom": {
                    "url": "https://hi-here/{x}/{y}/{z}",
                    "credits": "My Map",
                },
            },
            "invalid_custom": {
                "name": cls.genum(RasterTileServerNameEnum.CUSTOM),
                "custom": {
                    "url": "https://hi-there",
                    "credits": "My Map",
                },
            },
            "invalid_custom_02": {
                "name": cls.genum(RasterTileServerNameEnum.CUSTOM),
                "custom": {
                    "url": "https://hi-there/{{x}}/{{y}}/{{z}}",
                    "credits": "My Map",
                },
            },
        }
        # NOTE: _internal is for snake_case attributes, currently its same
        cls.tile_server_property_internal = cls.tile_server_property

    def _create_project_aoi_asset(self, project_asset_data: dict, **kwargs):
        with self.captureOnCommitCallbacks(execute=True):
            return create_project_aoi_asset_query(
                query_check_func=self.query_check,
                query=Mutation.CREATE_PROJECT_ASSET,
                project_asset_data={
                    **project_asset_data,
                    "inputType": self.genum(ProjectAssetInputTypeEnum.AOI_GEOMETRY),
                },
            )

    def _create_project_image_asset(self, project_asset_data: dict, **kwargs):
        with self.captureOnCommitCallbacks(execute=True):
            return create_project_image_asset_query(
                query_check_func=self.query_check,
                query=Mutation.CREATE_PROJECT_ASSET,
                project_asset_data={
                    **project_asset_data,
                    "inputType": self.genum(ProjectAssetInputTypeEnum.COVER_IMAGE),
                },
            )

    def _create_project_mutation(self, project_data: dict, **kwargs):
        with self.captureOnCommitCallbacks(execute=True):
            return self.query_check(
                query=Mutation.CREATE_PROJECT,
                variables={
                    "data": project_data,
                },
            )

    def _update_project_mutation(self, pk: str, project_data: dict, **kwargs):
        with self.captureOnCommitCallbacks(execute=True):
            return update_project_query(
                query_check_func=self.query_check,
                query=Mutation.UPDATE_PROJECT,
                pk=pk,
                project_data=project_data,
                **kwargs,
            )

    def _update_project_status_mutation(self, pk: str, project_data: dict, **kwargs):
        with self.captureOnCommitCallbacks(execute=True):
            return update_project_query(
                query_check_func=self.query_check,
                query=Mutation.UPDATE_PROJECT_STATUS,
                pk=pk,
                project_data=project_data,
                **kwargs,
            )

    def _update_processed_project_mutation(self, pk: str, project_data: dict, **kwargs):
        with self.captureOnCommitCallbacks(execute=True):
            return update_project_query(
                query_check_func=self.query_check,
                query=Mutation.UPDATE_PROCESSED_PROJECT,
                pk=pk,
                project_data=project_data,
                **kwargs,
            )

    @patch("apps.project.serializers.process_project_task.delay")
    def test_project_compare(self, mock_requests):
        # Defining user and base project data
        self.force_login(self.user)
        project_data = {
            **self.project_data,
            "projectType": self.genum(ProjectTypeEnum.COMPARE),
            "clientId": str(ULID()),
        }
        content = self._create_project_mutation(project_data)
        resp_data = content["data"]["createProject"]
        assert resp_data["errors"] is None, content

        project_id = resp_data["result"]["id"]
        project_client_id = resp_data["result"]["clientId"]

        # Creating AOI Project Asset
        project_asset_data = {
            "project": project_id,
            "clientId": str(ULID()),
        }
        content = self._create_project_aoi_asset(project_asset_data)
        resp_data = content["data"]["createProjectAsset"]
        assert resp_data["errors"] is None, content
        aoi_geometry_asset = resp_data["result"]

        # Creating Project Image Asset
        project_asset_data = {
            "project": project_id,
            "clientId": str(ULID()),
        }
        content = self._create_project_image_asset(project_asset_data)
        resp_data = content["data"]["createProjectAsset"]
        assert resp_data["errors"] is None, content
        image_asset = resp_data["result"]

        # Updating Project
        # fails as project type specifics has empty object as tile server property
        # project_data = {
        #     "clientId": project_client_id,
        #     "image": image_asset["id"],
        #     "projectTypeSpecifics": {
        #         "find": {
        #             "aoiGeometry": aoi_geometry_asset["id"],
        #             "zoomLevel": 15,
        #             "tileServerProperty": {},
        #             "tileServerBProperty": self.tile_server_property["valid_custom"],
        #         },
        #     },
        # }
        # content = self._update_project_mutation(project_id, project_data, assert_errors=True)
        # assert content["errors"] == [
        #     {
        #         "locations": [{"column": 42, "line": 2}],
        #         "message": "Variable '$data' got invalid value {} at 'data.projectTypeSpecifics.find.tileServerProperty'; Field 'name' of required type 'RasterTileServerNameEnum!' was not provided.",  # noqa: E501
        #     },
        #     {
        #         "locations": [{"column": 42, "line": 2}],
        #         "message": "Variable '$data' got invalid value {'aoiGeometry': '%s', 'zoomLevel': 15, 'tileServerProperty': {}, 'tileServerBProperty': {'name': 'CUSTOM', 'custom': {...}}} at 'data.projectTypeSpecifics.find'; Field 'tileServerBProperty' is not defined by type 'FindProjectPropertyInput'. Did you mean 'tileServerProperty'?"  # noqa: E501
        #         % aoi_geometry_asset["id"],
        #     },
        # ]

        # Updating Project
        # fails as project type specifics has partial data
        # project_data = {
        #     "clientId": project_client_id,
        #     "image": image_asset["id"],
        #     "projectTypeSpecifics": {
        #         "compare": {
        #             "aoiGeometry": aoi_geometry_asset["id"],
        #             "zoomLevel": 15,
        #             "tileServerProperty": self.tile_server_property["valid_custom"],
        #         },
        #     },
        # }
        # content = self._update_project_mutation(project_id, project_data, assert_errors=True)
        # assert content["errors"] == [
        #     {
        #         "locations": [{"column": 42, "line": 2}],
        #         "message": "Variable '$data' got invalid value {'aoiGeometry': '%s', 'zoomLevel': 15, 'tileServerProperty': {'name': 'CUSTOM', 'custom': {...}}} at 'data.projectTypeSpecifics.compare'; Field 'tileServerBProperty' of required type 'ProjectRasterTileServerConfigInput!' was not provided."  # noqa: E501
        #         % aoi_geometry_asset["id"],
        #     },
        # ]

        # Updating Project
        # fails as project type specifics has one invalid tile server property
        project_data = {
            "clientId": project_client_id,
            "image": image_asset["id"],
            "projectTypeSpecifics": {
                "compare": {
                    "aoiGeometry": aoi_geometry_asset["id"],
                    "zoomLevel": 15,
                    "tileServerProperty": self.tile_server_property["invalid_custom"],
                    "tileServerBProperty": self.tile_server_property["valid_custom"],
                },
            },
        }
        content = self._update_project_mutation(project_id, project_data)
        resp_data = content["data"]["updateProject"]
        assert resp_data["errors"] == [
            {
                "array_errors": None,
                "client_id": project_data["clientId"],
                "field": "nonFieldErrors",
                "messages": "The imagery url 'https://hi-there' must contain {x}, {y} (or {-y}) and {z} or the {quad_key} placeholders.",  # noqa: E501
                "object_errors": None,
                "pydantic_errors": None,
            },
        ], content

        # Updating Project
        # fails as project type specifics has one invalid tile server property
        project_data = {
            "clientId": project_client_id,
            "image": image_asset["id"],
            "projectTypeSpecifics": {
                "compare": {
                    "aoiGeometry": aoi_geometry_asset["id"],
                    "zoomLevel": 15,
                    "tileServerProperty": self.tile_server_property["invalid_custom_02"],
                    "tileServerBProperty": self.tile_server_property["valid_custom"],
                },
            },
        }
        content = self._update_project_mutation(project_id, project_data)
        resp_data = content["data"]["updateProject"]
        assert resp_data["errors"] == [
            {
                "array_errors": None,
                "client_id": project_client_id,
                "field": "nonFieldErrors",
                "messages": "The imagery url 'https://hi-there/{{x}}/{{y}}/{{z}}' must contain {x}, {y} (or {-y}) and {z} or the {quad_key} placeholders.",  # noqa: E501
                "object_errors": None,
                "pydantic_errors": None,
            },
        ], content

        # Updating Project
        project_data = {
            "clientId": project_client_id,
            "image": image_asset["id"],
            "verificationNumber": 10,
            "projectTypeSpecifics": {
                "compare": {
                    "aoiGeometry": aoi_geometry_asset["id"],
                    "zoomLevel": 15,
                    "tileServerProperty": self.tile_server_property["valid_custom"],
                    "tileServerBProperty": self.tile_server_property["valid_custom_02"],
                },
            },
        }
        content = self._update_project_mutation(project_id, project_data)
        resp_data = content["data"]["updateProject"]
        assert resp_data["errors"] is None, content

        latest_project = Project.objects.get(pk=project_id)
        assert latest_project.created_by_id == self.user.pk
        assert latest_project.modified_by_id == self.user.pk
        assert latest_project.image_id == int(image_asset["id"])
        assert latest_project.aoi_geometry_input_asset
        assert latest_project.aoi_geometry_input_asset.id == int(aoi_geometry_asset["id"])
        assert latest_project.project_type_specifics == {
            "aoi_geometry": aoi_geometry_asset["id"],
            "zoom_level": 15,
            "tile_server_property": self.tile_server_property_internal["valid_custom"],
            "tile_server_b_property": self.tile_server_property_internal["valid_custom_02"],
        }
        compare_project.CompareProjectProperty.model_validate(
            latest_project.project_type_specifics,
            context={"project_id": latest_project.pk},
        )

        # Updating Project:
        # Test project processing
        project_data = {
            "clientId": project_client_id,
            "status": self.genum(Project.Status.READY_TO_PROCESS),
        }
        content = self._update_project_status_mutation(project_id, project_data)
        resp_data = content["data"]["updateProjectStatus"]
        assert resp_data["errors"] is None, content
        assert resp_data["result"]["status"] == self.genum(Project.Status.READY_TO_PROCESS)
        latest_project.refresh_from_db()
        assert latest_project.processing_status is None

        mock_requests.assert_called_once()
        mock_requests.assert_has_calls([call(int(project_id))])

        process_project_task(int(project_id))

        class TaskGroupSpecificsType(typing.TypedDict):
            x_max: int
            x_min: int
            y_max: int
            y_min: int

        class TaskGroupType(typing.TypedDict):
            firebase_id: str
            number_of_tasks: int
            required_count: int
            total_area: float
            project_type_specifics: TaskGroupSpecificsType

        expected_task_groups: list[TaskGroupType] = [
            {
                "firebase_id": "g101",
                "number_of_tasks": 18,
                "required_count": 18 * 10,
                "total_area": 210.10735845202447,
                "project_type_specifics": {
                    "x_max": 24152,
                    "x_min": 24147,
                    "y_max": 13755,
                    "y_min": 13753,
                },
            },
            {
                "firebase_id": "g102",
                "number_of_tasks": 24,
                "required_count": 24 * 10,
                "total_area": 280.2915392364502,
                "project_type_specifics": {
                    "x_max": 24153,
                    "x_min": 24146,
                    "y_max": 13758,
                    "y_min": 13756,
                },
            },
            {
                "firebase_id": "g103",
                "number_of_tasks": 24,
                "required_count": 24 * 10,
                "total_area": 280.4398676951218,
                "project_type_specifics": {
                    "x_max": 24153,
                    "x_min": 24146,
                    "y_max": 13761,
                    "y_min": 13759,
                },
            },
            {
                "firebase_id": "g104",
                "number_of_tasks": 6,
                "required_count": 6 * 10,
                "total_area": 70.14703242812156,
                "project_type_specifics": {
                    "x_max": 24150,
                    "x_min": 24149,
                    "y_max": 13764,
                    "y_min": 13762,
                },
            },
        ]
        expected_last_5_tasks = [
            {
                "firebase_id": "15-24147-13753",
                "project_type_specifics": {
                    "tile_x": 24147,
                    "tile_y": 13753,
                },
            },
            {
                "firebase_id": "15-24147-13754",
                "project_type_specifics": {
                    "tile_x": 24147,
                    "tile_y": 13754,
                },
            },
            {
                "firebase_id": "15-24147-13755",
                "project_type_specifics": {
                    "tile_x": 24147,
                    "tile_y": 13755,
                },
            },
            {
                "firebase_id": "15-24148-13753",
                "project_type_specifics": {
                    "tile_x": 24148,
                    "tile_y": 13753,
                },
            },
            {
                "firebase_id": "15-24148-13754",
                "project_type_specifics": {
                    "tile_x": 24148,
                    "tile_y": 13754,
                },
            },
        ]

        latest_project.refresh_from_db()
        project_task_group_qs = ProjectTaskGroup.objects.filter(project=latest_project)
        project_task_qs = ProjectTask.objects.filter(task_group__project=latest_project)

        assert {
            "required_results": sum(task_group["required_count"] for task_group in expected_task_groups),
            "tasks_groups_count": project_task_group_qs.count(),
            "tasks_groups": list(
                project_task_group_qs.order_by("id").values(
                    "firebase_id",
                    "number_of_tasks",
                    "required_count",
                    "total_area",
                    "project_type_specifics",
                ),
            ),
            "tasks_count": project_task_qs.count(),
            "tasks": list(
                project_task_qs.order_by("id").values(
                    "firebase_id",
                    "project_type_specifics",
                )[:5],
            ),
            "status": latest_project.status,
            "processing_status": latest_project.processing_status,
        } == {
            "required_results": latest_project.required_results,
            "tasks_groups_count": len(expected_task_groups),
            "tasks_groups": expected_task_groups,
            "tasks_count": 72,
            "tasks": expected_last_5_tasks,
            "status": Project.Status.PROCESSED,
            "processing_status": Project.ProcessingStatus.COMPLETED,
        }

        # Updating Project: Status change
        # fails as tutorial is not set when publishing project
        project_data = {
            "clientId": project_client_id,
            "status": self.genum(Project.Status.READY_TO_PUBLISH),
        }
        content = self._update_project_status_mutation(project_id, project_data)
        resp_data = content["data"]["updateProjectStatus"]
        assert resp_data["errors"] == [
            {
                "array_errors": None,
                "client_id": project_client_id,
                "field": "tutorial",
                "messages": "Tutorial is required before publishing a project.",
                "object_errors": None,
                "pydantic_errors": None,
            },
        ], content

        # Updating Processed Project:
        # Attaching tutorial
        project_data = {
            "clientId": project_client_id,
            "tutorial": str(self.compare_tutorial.id),
        }
        content = self._update_processed_project_mutation(project_id, project_data)
        resp_data = content["data"]["updateProcessedProject"]
        assert resp_data["errors"] is None, content
        assert resp_data["result"]["tutorialId"] == str(self.compare_tutorial.id)
        # project is not sync to firebase
        project_ref = self.firebase_helper.ref(
            Config.FirebaseKeys.project(latest_project.firebase_id),
        )
        fb_project: typing.Any = project_ref.get()
        assert fb_project is None

        # Updating Processed Project:
        # Publishing project
        project_data = {
            "clientId": project_client_id,
            "status": self.genum(Project.Status.READY_TO_PUBLISH),
        }
        content = self._update_project_status_mutation(project_id, project_data)
        resp_data = content["data"]["updateProjectStatus"]
        assert resp_data["errors"] is None, content
        assert resp_data["result"]["status"] == self.genum(Project.Status.READY_TO_PUBLISH)

        latest_project.refresh_from_db()
        assert latest_project.processing_status == Project.ProcessingStatus.COMPLETED

        # project is sync to firebase after publish
        fb_project: typing.Any = project_ref.get()
        assert fb_project is not None

    @patch("apps.project.serializers.process_project_task.delay")
    def test_project_street(self, mock_requests):
        self.force_login(self.user)
        project_data = {
            **self.project_data,
            "clientId": str(ULID()),
            "projectType": self.genum(ProjectTypeEnum.STREET),
        }
        content = self._create_project_mutation(project_data)
        resp_data = content["data"]["createProject"]
        assert resp_data["errors"] is None, content

        project_id = resp_data["result"]["id"]
        project_client_id = resp_data["result"]["clientId"]

        # Creating AOI Project Asset
        project_asset_data = {
            "project": project_id,
            "clientId": str(ULID()),
        }

        content = self._create_project_aoi_asset(project_asset_data, assert_errors=True)
        resp_data = content["data"]["createProjectAsset"]
        assert resp_data["errors"] is None, content
        aoi_geometry_asset = resp_data["result"]

        # Creating Project Image Asset
        project_asset_data = {
            "project": project_id,
            "clientId": str(ULID()),
        }
        content = self._create_project_image_asset(project_asset_data, assert_errors=True)
        resp_data = content["data"]["createProjectAsset"]
        assert resp_data["errors"] is None, content
        image_asset = resp_data["result"]

        # Updating Project
        project_data = {
            "clientId": project_client_id,
            "image": image_asset["id"],
            "verificationNumber": 10,
            "projectTypeSpecifics": {
                "street": {
                    "aoiGeometry": aoi_geometry_asset["id"],
                    "customOptions": {
                        "clientId": str(ULID()),
                        "description": "Street project description",
                        "icon": self.genum(IconEnum.ADD_OUTLINE),
                        "iconColor": "#FF0000",
                        "title": "Street Project Title",
                        "value": 1,
                        "subOptions": [
                            {
                                "clientId": str(ULID()),
                                "value": 1,
                                "description": "Street sub option description",
                            },
                        ],
                    },
                    "mapillaryImageFilters": {
                        "isPano": True,
                        "creatorId": None,
                        "organizationId": None,
                        "startTime": None,
                        "endTime": None,
                        "randomizeOrder": False,
                        "samplingThreshold": None,
                    },
                },
            },
        }
        content = self._update_project_mutation(project_id, project_data)
        resp_data = content["data"]["updateProject"]
        assert resp_data["errors"] is None, content

        latest_project = Project.objects.get(pk=project_id)
        assert latest_project.created_by_id == self.user.pk
        assert latest_project.modified_by_id == self.user.pk
        assert latest_project.image_id == int(image_asset["id"])
        assert latest_project.project_type_specifics is not None
        assert latest_project.aoi_geometry_input_asset
        assert latest_project.aoi_geometry_input_asset.id == int(aoi_geometry_asset["id"])

        street_project.StreetProjectProperty.model_validate(
            latest_project.project_type_specifics,
            context={"project_id": latest_project.pk},
        )

        # Updating Project:
        # Test project processing
        project_data = {
            "clientId": project_client_id,
            "status": self.genum(Project.Status.READY_TO_PROCESS),
        }
        content = self._update_project_status_mutation(project_id, project_data)
        resp_data = content["data"]["updateProjectStatus"]
        assert resp_data["errors"] is None, content
        assert resp_data["result"]["status"] == self.genum(Project.Status.READY_TO_PROCESS)

        mock_requests.assert_called_once()
        mock_requests.assert_has_calls([call(int(project_id))])

import typing
from pathlib import Path
from unittest.mock import call, patch

from django.conf import settings
from django.core.files.temp import NamedTemporaryFile

from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.project.models import (
    Project,
    ProjectAssetMimetypeEnum,
    ProjectAssetTypeEnum,
    ProjectTask,
    ProjectTaskGroup,
    ProjectTypeEnum,
)
from apps.project.project_types.tile_map_service.compare import project as compare_project
from apps.project.tasks import process_project_task
from apps.user.factories import UserFactory
from main.tests import TestCase
from utils.geo.tile_server.config import TileServerNameEnum

BASE_DIR = Path(__file__).resolve().parent


def create_project_image_asset_query(
    *,
    query_check_func: typing.Callable,
    query: str,
    project_asset_data: dict,
    **kwargs,
) -> dict:
    with (
        NamedTemporaryFile(dir=settings.TEMP_DIR) as image_file,
    ):
        # Mock image
        image_file.write(b"base64image")
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
        Path(BASE_DIR / "data/ring-road.geojson").open() as geo_file,
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


def create_project_query(
    *,
    query_check_func: typing.Callable,
    query: str,
    project_data: dict,
    **kwargs,
) -> dict:
    return query_check_func(
        query,
        variables={
            "data": project_data,
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
                type
                mimetype
                projectId
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
                projectType
                requestingOrganizationId
                requestingOrganization {
                  id
                  name
                }
                name
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
                projectType
                requestingOrganizationId
                requestingOrganization {
                  id
                  name
                }
                name
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
                projectType
                requestingOrganizationId
                requestingOrganization {
                  id
                  name
                }
                name
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
              }
            }
          }
        }
    """


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
        return create_project_aoi_asset_query(
            query_check_func=self.query_check,
            query=Mutation.CREATE_PROJECT_ASSET,
            project_asset_data=project_asset_data,
        )

    def _create_project_image_asset(self, project_asset_data: dict, **kwargs):
        return create_project_image_asset_query(
            query_check_func=self.query_check,
            query=Mutation.CREATE_PROJECT_ASSET,
            project_asset_data=project_asset_data,
        )

    def _create_project_mutation(self, project_data: dict, **kwargs):
        return create_project_query(
            query_check_func=self.query_check,
            query=Mutation.CREATE_PROJECT,
            project_data=project_data,
        )

    def _update_project_mutation(self, pk: str, project_data: dict, **kwargs):
        return update_project_query(
            query_check_func=self.query_check,
            query=Mutation.UPDATE_PROJECT,
            pk=pk,
            project_data=project_data,
            **kwargs,
        )

    def test_project_create(self):
        project_data = {
            "projectType": self.genum(ProjectTypeEnum.FIND),
            "requestingOrganization": self.organization.pk,
            "name": "New Project 101",
            "lookFor": "Buildings",
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

        latest_project = Project.objects.get(pk=resp_data["result"]["id"])
        assert latest_project.created_by_id == self.user.pk
        assert latest_project.modified_by_id == self.user.pk
        assert resp_data == self.g_mutation_response(
            ok=True,
            result=dict(
                id=self.gID(latest_project.pk),
                projectType=self.genum(ProjectTypeEnum.FIND),
                requestingOrganizationId=self.gID(latest_project.requesting_organization.pk),
                requestingOrganization=dict(
                    id=self.gID(latest_project.requesting_organization.pk),
                    name=latest_project.requesting_organization.name,
                ),
                name=latest_project.name,
                lookFor=latest_project.look_for,
                additionalInfoUrl=latest_project.additional_info_url,
                description=latest_project.description,
                verificationNumber=3,
                groupSize=10,
                maxTasksPerUser=10,
                isFeatured=latest_project.is_featured,
                status=self.genum(Project.Status.DRAFT),
                processingStatus=None,
                progress=0,
            ),
        ), content

    def test_project_update(self):
        proj = ProjectFactory.create(
            **self.user_resource_kwargs,
            project_type=ProjectTypeEnum.FIND,
            requesting_organization=self.organization,
            name="New Project 101",
            look_for="Buildings",
            additional_info_url="https://hi-there/about.html",
            description="The new **project** from hi-there.",
            project_type_specifics=None,
        )

        project_data = {
            "requestingOrganization": self.organization.pk,
            "name": "New Project 101 - Updated",
            "lookFor": "Buildings and Houses",
            "additionalInfoUrl": "https://hi-there/about.html?code=1",
            "description": "The new updated **project** from hi-there.",
            "verificationNumber": 2,
            "groupSize": 16,
            "maxTasksPerUser": 11,
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
                projectType=self.genum(ProjectTypeEnum.FIND),
                requestingOrganizationId=self.gID(latest_project.requesting_organization.pk),
                requestingOrganization=dict(
                    id=self.gID(latest_project.requesting_organization.pk),
                    name=latest_project.requesting_organization.name,
                ),
                name=latest_project.name,
                lookFor=latest_project.look_for,
                additionalInfoUrl=latest_project.additional_info_url,
                description=latest_project.description,
                verificationNumber=latest_project.verification_number,
                groupSize=latest_project.group_size,
                maxTasksPerUser=latest_project.max_tasks_per_user,
                isFeatured=latest_project.is_featured,
                status=self.genum(Project.Status.DRAFT),
                processingStatus=None,
                progress=0,
            ),
        ), content

        # Updating Project: Status change
        # fails as project specifics is required when changing status to "marked as ready"
        project_data = {
            "status": self.genum(Project.Status.MARKED_AS_READY),
        }
        content = self._update_project_mutation(str(latest_project.pk), project_data)
        assert content["data"]["updateProject"]["errors"] == [
            {
                "array_errors": None,
                "client_id": None,
                "field": "projectTypeSpecifics",
                "messages": "Configuration not provided for Find",
                "object_errors": None,
                "pydantic_errors": None,
            },
        ]

        # Creating AOI Project Asset
        project_asset_data = {
            "project": str(latest_project.pk),
            "mimetype": self.genum(ProjectAssetMimetypeEnum.GEOJSON),
            "type": self.genum(ProjectAssetTypeEnum.INPUT),
        }
        content = self._create_project_aoi_asset(project_asset_data, assert_errors=True)
        resp_data = content["data"]["createProjectAsset"]
        assert resp_data["errors"] is None, content
        aoi_geometry_asset = resp_data["result"]

        # Creating Project Image Asset
        project_asset_data = {
            "project": str(latest_project.pk),
            "mimetype": self.genum(ProjectAssetMimetypeEnum.IMAGE_JPEG),
            "type": self.genum(ProjectAssetTypeEnum.INPUT),
        }
        content = self._create_project_image_asset(project_asset_data, assert_errors=True)
        resp_data = content["data"]["createProjectAsset"]
        assert resp_data["errors"] is None, content
        image_asset = resp_data["result"]

        # Updating Project: with empty object as project type specifics
        project_data = {
            "projectTypeSpecifics": {},
        }
        content = self._update_project_mutation(str(latest_project.pk), project_data, assert_errors=True)
        assert content["errors"] == [
            {
                "message": "OneOf Input Object 'ProjectTypeSpecificInput' must specify exactly one key.",
            },
        ]

        # Updating Project: with valid but mismatching project type specifics
        project_data = {
            "image": image_asset["id"],
            "projectTypeSpecifics": {
                "compare": {
                    "aoiGeometry": aoi_geometry_asset["id"],
                    "zoomLevel": 15,
                    "tileServerProperty": {
                        "name": self.genum(TileServerNameEnum.CUSTOM),
                        "custom": {
                            "url": "https://hi-there/{x}/{y}/{z}",
                            "credits": "My Map",
                        },
                    },
                    "tileServerBProperty": {
                        "name": self.genum(TileServerNameEnum.CUSTOM),
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
                "client_id": None,
                "messages": "Configuration not provided for Find",
                "object_errors": None,
                "array_errors": None,
                "pydantic_errors": None,
            },
        ]

        # Updating Project: with valid project type specifics
        project_data = {
            "image": image_asset["id"],
            "projectTypeSpecifics": {
                "find": {
                    "aoiGeometry": aoi_geometry_asset["id"],
                    "zoomLevel": 15,
                    "tileServerProperty": {
                        "name": self.genum(TileServerNameEnum.CUSTOM),
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
        assert latest_project.project_type_specifics == {
            "zoom_level": 15,
            "aoi_geometry": aoi_geometry_asset["id"],
            "tile_server_property": {
                "name": TileServerNameEnum.CUSTOM.value,
                "custom": {
                    "credits": "My Map",
                    "url": "https://hi-there/{x}/{y}/{z}",
                },
            },
        }

        # Updating Project: Status change
        project_data = {
            "status": self.genum(Project.Status.MARKED_AS_READY),
        }
        content = self._update_project_mutation(str(latest_project.pk), project_data)
        assert content["data"]["updateProject"]["errors"] is None


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

        cls.project_data = {
            "name": "New Project 101",
            "requestingOrganization": cls.organization.pk,
            "lookFor": "Buildings",
        }

        cls.tile_server_property = {
            "valid_custom": {
                "name": cls.genum(TileServerNameEnum.CUSTOM),
                "custom": {
                    "url": "https://hi-there/{x}/{y}/{z}",
                    "credits": "My Map",
                },
            },
            "valid_custom_02": {
                "name": cls.genum(TileServerNameEnum.CUSTOM),
                "custom": {
                    "url": "https://hi-here/{x}/{y}/{z}",
                    "credits": "My Map",
                },
            },
            "invalid_custom": {
                "name": cls.genum(TileServerNameEnum.CUSTOM),
                "custom": {
                    "url": "https://hi-there",
                    "credits": "My Map",
                },
            },
            "invalid_custom_02": {
                "name": cls.genum(TileServerNameEnum.CUSTOM),
                "custom": {
                    "url": "https://hi-there/{{x}}/{{y}}/{{z}}",
                    "credits": "My Map",
                },
            },
        }
        # NOTE: _internal is for snake_case attributes, currently its same
        cls.tile_server_property_internal = cls.tile_server_property

    def _create_project_aoi_asset(self, project_asset_data: dict, **kwargs):
        return create_project_aoi_asset_query(
            query_check_func=self.query_check,
            query=Mutation.CREATE_PROJECT_ASSET,
            project_asset_data=project_asset_data,
        )

    def _create_project_image_asset(self, project_asset_data: dict, **kwargs):
        return create_project_image_asset_query(
            query_check_func=self.query_check,
            query=Mutation.CREATE_PROJECT_ASSET,
            project_asset_data=project_asset_data,
        )

    def _create_project_mutation(self, project_data: dict, **kwargs):
        with self.captureOnCommitCallbacks(execute=True):
            return create_project_query(
                query_check_func=self.query_check,
                query=Mutation.CREATE_PROJECT,
                project_data=project_data,
                **kwargs,
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

    @patch("apps.project.serializers.process_project_task.delay")
    def test_project_compare(self, mock_requests):
        # Defining user and base project data
        self.force_login(self.user)
        project_data = {
            **self.project_data,
            "projectType": self.genum(ProjectTypeEnum.COMPARE),
        }
        content = self._create_project_mutation(project_data)
        resp_data = content["data"]["createProject"]
        assert resp_data["errors"] is None, content

        project_id = resp_data["result"]["id"]

        # Creating AOI Project Asset
        project_asset_data = {
            "project": project_id,
            "mimetype": self.genum(ProjectAssetMimetypeEnum.GEOJSON),
            "type": self.genum(ProjectAssetTypeEnum.INPUT),
        }
        content = self._create_project_aoi_asset(project_asset_data, assert_errors=True)
        resp_data = content["data"]["createProjectAsset"]
        assert resp_data["errors"] is None, content
        aoi_geometry_asset = resp_data["result"]

        # Creating Project Image Asset
        project_asset_data = {
            "project": project_id,
            "mimetype": self.genum(ProjectAssetMimetypeEnum.IMAGE_JPEG),
            "type": self.genum(ProjectAssetTypeEnum.INPUT),
        }
        content = self._create_project_image_asset(project_asset_data, assert_errors=True)
        resp_data = content["data"]["createProjectAsset"]
        assert resp_data["errors"] is None, content
        image_asset = resp_data["result"]

        # Updating Project
        # fails as project type specifics has empty object as tile server property
        project_data = {
            "image": image_asset["id"],
            "projectTypeSpecifics": {
                "find": {
                    "aoiGeometry": aoi_geometry_asset["id"],
                    "zoomLevel": 15,
                    "tileServerProperty": {},
                    "tileServerBProperty": self.tile_server_property["valid_custom"],
                },
            },
        }
        content = self._update_project_mutation(project_id, project_data, assert_errors=True)

        # Updating Project
        # fails as project type specifics has partial data
        project_data = {
            "image": image_asset["id"],
            "projectTypeSpecifics": {
                "compare": {
                    "aoiGeometry": aoi_geometry_asset["id"],
                    "zoomLevel": 15,
                    "tileServerProperty": self.tile_server_property["valid_custom"],
                },
            },
        }
        content = self._update_project_mutation(project_id, project_data, assert_errors=True)

        # Updating Project
        # fails as project type specifics has one invalid tile server property
        project_data = {
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
        assert resp_data["errors"] is not None, content

        # Updating Project
        # fails as project type specifics has one invalid tile server property
        project_data = {
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
        assert resp_data["errors"] is not None, content

        # Updating Project
        project_data = {
            "image": image_asset["id"],
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
            "status": self.genum(Project.Status.MARKED_AS_READY),
        }
        content = self._update_project_mutation(project_id, project_data)
        resp_data = content["data"]["updateProject"]
        assert resp_data["errors"] is None, content
        assert resp_data["result"]["status"] == self.genum(Project.Status.MARKED_AS_READY)
        assert resp_data["result"]["processingStatus"] is None

        mock_requests.assert_called_once()
        mock_requests.assert_has_calls([call(int(project_id))])

        process_project_task(int(project_id))

        expected_task_groups = [
            {
                "number_of_tasks": 18,
                "project_type_specifics": {
                    "x_max": 24152,
                    "x_min": 24147,
                    "y_max": 13755,
                    "y_min": 13753,
                },
            },
            {
                "number_of_tasks": 24,
                "project_type_specifics": {
                    "x_max": 24153,
                    "x_min": 24146,
                    "y_max": 13758,
                    "y_min": 13756,
                },
            },
            {
                "number_of_tasks": 24,
                "project_type_specifics": {
                    "x_max": 24153,
                    "x_min": 24146,
                    "y_max": 13761,
                    "y_min": 13759,
                },
            },
            {
                "number_of_tasks": 6,
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
                "project_type_specifics": {
                    "tile_x": 24147,
                    "tile_y": 13753,
                    "url": "https://hi-there/24147/13753/15",
                    "url_b": "https://hi-here/24147/13753/15",
                },
            },
            {
                "project_type_specifics": {
                    "tile_x": 24147,
                    "tile_y": 13754,
                    "url": "https://hi-there/24147/13754/15",
                    "url_b": "https://hi-here/24147/13754/15",
                },
            },
            {
                "project_type_specifics": {
                    "tile_x": 24147,
                    "tile_y": 13755,
                    "url": "https://hi-there/24147/13755/15",
                    "url_b": "https://hi-here/24147/13755/15",
                },
            },
            {
                "project_type_specifics": {
                    "tile_x": 24148,
                    "tile_y": 13753,
                    "url": "https://hi-there/24148/13753/15",
                    "url_b": "https://hi-here/24148/13753/15",
                },
            },
            {
                "project_type_specifics": {
                    "tile_x": 24148,
                    "tile_y": 13754,
                    "url": "https://hi-there/24148/13754/15",
                    "url_b": "https://hi-here/24148/13754/15",
                },
            },
        ]

        latest_project.refresh_from_db()
        project_task_group_qs = ProjectTaskGroup.objects.filter(project=latest_project)
        project_task_qs = ProjectTask.objects.filter(task_group__project=latest_project)

        assert {
            "tasks_groups_count": project_task_group_qs.count(),
            "tasks_groups": list(
                project_task_group_qs.order_by("id").values(
                    "number_of_tasks",
                    "project_type_specifics",
                ),
            ),
            "tasks_count": project_task_qs.count(),
            "tasks": list(
                project_task_qs.order_by("id").values(
                    "project_type_specifics",
                )[:5],
            ),
            "status": latest_project.status,
            "processing_status": latest_project.processing_status,
        } == {
            "tasks_groups_count": len(expected_task_groups),
            "tasks_count": 72,
            "tasks_groups": expected_task_groups,
            "tasks": expected_last_5_tasks,
            "status": Project.Status.READY,
            "processing_status": Project.ProcessingStatus.COMPLETED,
        }

        # Updating Processed Project:
        # Test project publishing
        project_data = {
            "status": self.genum(Project.Status.PUBLISHED),
        }
        content = self._update_processed_project_mutation(project_id, project_data)
        resp_data = content["data"]["updateProcessedProject"]
        assert resp_data["errors"] is None, content
        assert resp_data["result"]["status"] == self.genum(Project.Status.PUBLISHED)
        assert resp_data["result"]["processingStatus"] == self.genum(Project.ProcessingStatus.COMPLETED)

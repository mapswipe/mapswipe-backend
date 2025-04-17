import typing
from pathlib import Path

from django.conf import settings
from django.core.files.temp import NamedTemporaryFile

from apps.project.factories import OrganizationFactory
from apps.project.models import Project, ProjectTask, ProjectTaskGroup, ProjectTypeEnum
from apps.project.project_types.tile_map_service.change_detection import project as change_detection_project
from apps.user.factories import UserFactory
from main.tests import TestCase
from utils.geo.tile_server.config import TileServerNameEnum

BASE_DIR = Path(__file__).resolve().parent


def create_project_query(
    *,
    query_check_func: typing.Callable,
    query: str,
    project_data: dict,
    empty_geo_file=False,
    **kwargs,
) -> dict:
    with (
        NamedTemporaryFile(dir=settings.TEMP_DIR) as image_file,
        Path(BASE_DIR / "data/ring-road.geojson").open() as geo_file,
    ):
        # Fake image
        image_file.write(b"base64image")
        image_file.seek(0)

        if empty_geo_file:
            # Empty file
            geo_file.seek(0, 2)

        return query_check_func(
            query,
            variables={
                "data": project_data,
            },
            files={
                "imageFile": image_file,
                "geoFile": geo_file,
            },
            map={
                "imageFile": ["variables.data.image"],
                "geoFile": ["variables.data.geometryFile"],
            },
            **kwargs,
        )


class TestProjectMutation(TestCase):
    class Mutation:
        CREATE_PROJECT = """
            mutation CreateProject($data: ProjectInput!) {
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
                    name
                    projectType
                    organizationId
                    organization {
                      id
                      name
                    }
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

        cls.organization = OrganizationFactory.create(**cls.user_resource_kwargs)

    def test_project_create(self):
        project_data = {
            "name": "New Project 101",
            "organization": self.organization.pk,
            "projectType": self.genum(ProjectTypeEnum.CHANGE_DETECTION),
            "groupSize": 15,
            "verificationNumber": 1,
            "lookFor": "Buildings",
            "projectTypeSpecifics": {
                "classification": {
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

        def _query():
            return create_project_query(
                query_check_func=self.query_check,
                query=self.Mutation.CREATE_PROJECT,
                project_data=project_data,
            )

        # Without authentication -----
        content = _query()
        assert content["data"]["createProject"]["messages"] == [
            {
                "code": None,
                "field": "createProject",
                "kind": "PERMISSION",
                "message": "User is not authenticated.",
            },
        ], content

        # With authentication -----
        self.force_login(self.user)
        content = _query()
        resp_data = content["data"]["createProject"]
        assert resp_data["errors"] is not None, content

        # Fix the error and try again
        project_data["projectType"] = self.genum(ProjectTypeEnum.BUILD_AREA)
        content = _query()
        resp_data = content["data"]["createProject"]
        assert resp_data["errors"] is None, content

        # Fetch the new project from database
        latest_project = Project.objects.get(pk=resp_data["result"]["id"])

        # Validate response values
        assert resp_data == self.g_mutation_response(
            ok=True,
            result=dict(
                id=self.gID(latest_project.pk),
                name=latest_project.name,
                organization=dict(
                    id=self.gID(latest_project.organization.pk),
                    name=latest_project.organization.name,
                ),
                organizationId=self.gID(latest_project.organization.pk),
                projectType=self.genum(ProjectTypeEnum.BUILD_AREA),
            ),
        ), content

        # Validate database values
        assert latest_project.created_by_id == self.user.pk
        assert latest_project.modified_by_id == self.user.pk
        assert latest_project.project_type_specifics == {
            "zoom_level": 15,
            "tile_server_property": {
                "name": TileServerNameEnum.CUSTOM.value,
                "custom": {
                    "credits": "My Map",
                    "url": "https://hi-there/{x}/{y}/{z}",
                },
            },
        }


class TestProjectTypeMutation(TestCase):
    class Mutation:
        CREATE_PROJECT = """
            mutation CreateProject($data: ProjectInput!) {
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
                    name
                    projectType
                    organizationId
                    organization {
                      id
                      name
                    }
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

        cls.organization = OrganizationFactory.create(**cls.user_resource_kwargs)
        cls.project_data = {
            "name": "New Project 101",
            "organization": cls.organization.pk,
            "groupSize": 15,
            "verificationNumber": 1,
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

    def _query(self, project_data, empty_geo_file=False, **kwargs):
        with self.captureOnCommitCallbacks(execute=True):
            return create_project_query(
                query_check_func=self.query_check,
                query=self.Mutation.CREATE_PROJECT,
                project_data=project_data,
                empty_geo_file=empty_geo_file,
                **kwargs,
            )

    def test_project_change_detection(self):
        self.force_login(self.user)
        project_data = {
            **self.project_data,
            "projectType": self.genum(ProjectTypeEnum.CHANGE_DETECTION),
        }

        # Pydantic error (with valid projectTypeSpecifics type but invalid data)
        project_data = {
            **project_data,
            "projectTypeSpecifics": {
                "classification": {  # NOTE: Different project type
                    "zoomLevel": 15,
                    "tileServerProperty": self.tile_server_property["valid_custom"],
                },
            },
        }

        content = self._query(project_data)
        resp_data = content["data"]["createProject"]
        assert resp_data["errors"] == [
            {
                "field": "projectTypeSpecifics",
                "client_id": None,
                "messages": "Configuration not provided for: Compare",
                "object_errors": None,
                "array_errors": None,
                "pydantic_errors": None,
            },
        ], content

        content = self._query(project_data, empty_geo_file=True)
        resp_data = content["data"]["createProject"]
        assert resp_data["errors"] == [
            {
                "field": "geometryFile",
                "client_id": None,
                "messages": "The submitted file is empty.",
                "object_errors": None,
                "array_errors": None,
                "pydantic_errors": None,
            },
        ], content

        # GraphQL error (without projectTypeSpecifics)
        project_data.pop("projectTypeSpecifics")
        content = self._query(project_data, assert_errors=True)

        # GraphQL error (with invalid projectTypeSpecifics)
        project_data = {
            **project_data,
            "projectTypeSpecifics": {},
        }
        content = self._query(project_data, assert_errors=True)

        # GraphQL error (with invalid projectTypeSpecifics) - Try 1
        project_data = {
            **project_data,
            "projectTypeSpecifics": {
                "classification": {},
            },
        }
        content = self._query(project_data, assert_errors=True)

        # GraphQL error (with invalid projectTypeSpecifics) - Try 2
        project_data = {
            **project_data,
            "projectTypeSpecifics": {
                "classification": {
                    "zoomLevel": 15,
                    "tileServerProperty": {},
                },
            },
        }
        content = self._query(project_data, assert_errors=True)

        # GraphQL error (Partial data)
        project_data = {
            **project_data,
            "projectTypeSpecifics": {
                "changeDetection": {
                    "zoomLevel": 15,
                    "tileServerProperty": self.tile_server_property["valid_custom"],
                },
            },
        }
        content = self._query(project_data, assert_errors=True)

        # Pydantic validation error
        project_data = {
            **project_data,
            "projectTypeSpecifics": {
                "changeDetection": {
                    "zoomLevel": 15,
                    "tileServerProperty": self.tile_server_property["invalid_custom"],
                    "tileServerBProperty": self.tile_server_property["valid_custom"],
                },
            },
        }
        content = self._query(project_data)
        resp_data = content["data"]["createProject"]
        assert resp_data["errors"] is not None, content

        # Pydantic validation error
        project_data = {
            **project_data,
            "projectTypeSpecifics": {
                "changeDetection": {
                    "zoomLevel": 15,
                    "tileServerProperty": self.tile_server_property["invalid_custom_02"],
                    "tileServerBProperty": self.tile_server_property["valid_custom"],
                },
            },
        }
        content = self._query(project_data)
        resp_data = content["data"]["createProject"]
        assert resp_data["errors"] is not None, content

        # Success
        project_data = {
            **project_data,
            "projectTypeSpecifics": {
                "changeDetection": {
                    "zoomLevel": 15,
                    "tileServerProperty": self.tile_server_property["valid_custom"],
                    "tileServerBProperty": self.tile_server_property["valid_custom_02"],
                },
            },
        }

        content = self._query(project_data)
        resp_data = content["data"]["createProject"]
        assert resp_data["errors"] is None, content
        # -- Compare with DB
        latest_project = Project.objects.get(pk=resp_data["result"]["id"])
        assert latest_project.created_by_id == self.user.pk
        assert latest_project.modified_by_id == self.user.pk
        assert latest_project.project_type_specifics == {
            "zoom_level": 15,
            "tile_server_property": self.tile_server_property_internal["valid_custom"],
            "tile_server_b_property": self.tile_server_property_internal["valid_custom_02"],
        }
        change_detection_project.ChangeDetectionProjectProperty.model_validate(latest_project.project_type_specifics)

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
        } == {
            "tasks_groups_count": len(expected_task_groups),
            "tasks_count": 72,
            "tasks_groups": expected_task_groups,
            "tasks": expected_last_5_tasks,
        }

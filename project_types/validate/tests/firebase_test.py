import typing

from pyfirebase_mapswipe import utils as firebase_utils

from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.project.models import Project, ProjectTypeEnum
from apps.tutorial.factories import TutorialFactory
from apps.user.factories import UserFactory
from main.tests import TestCase
from project_types.validate.project import VALIDATE_FALLBACK_RASTER_LAYER, ValidateProject
from project_types.validate.tutorial import ValidateTutorial

POST_EVENT_TILE_SERVER_PROPERTY = {
    "name": "CUSTOM",
    "custom": {
        "credits": "Post-event credits",
        "url": "https://post-event.example.com/{z}/{x}/{y}.png",
    },
}

PRE_EVENT_TILE_SERVER_PROPERTY = {
    "name": "CUSTOM",
    "custom": {
        "credits": "Pre-event credits",
        "url": "https://pre-event.example.com/{z}/{x}/{y}.png",
    },
}

POST_EVENT_TILE_SERVER = {
    "name": "custom",
    "credits": "Post-event credits",
    "url": "https://post-event.example.com/{z}/{x}/{y}.png",
    "apiKey": "",
    "wmtsLayerName": None,
}

PRE_EVENT_TILE_SERVER = {
    "name": "custom",
    "credits": "Pre-event credits",
    "url": "https://pre-event.example.com/{z}/{x}/{y}.png",
    "apiKey": "",
    "wmtsLayerName": None,
}

FALLBACK_TILE_SERVER = {
    "name": "custom",
    "credits": "n/a",
    "url": VALIDATE_FALLBACK_RASTER_LAYER,
    "apiKey": "",
    "wmtsLayerName": None,
}

TILE_SERVER_KEYS = ("tileServer", "preEventTileServer", "postEventTileServer")


class TestValidateFirebaseTileServers(TestCase):
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

    def _create_project(self, **extra_project_type_specifics: typing.Any) -> Project:
        return ProjectFactory.create(
            **self.user_resource_kwargs,
            requesting_organization=self.organization,
            project_type=ProjectTypeEnum.VALIDATE,
            project_type_specifics={
                "object_source": {
                    "source_type": "TASKING_MANAGER",
                    "tasking_manager_project_id": "1234",
                    "ohsome_filter": "building=*",
                },
                "tile_server_property": POST_EVENT_TILE_SERVER_PROPERTY,
                **extra_project_type_specifics,
            },
        )

    def _get_tile_servers(self, project: Project) -> tuple[dict[str, typing.Any], dict[str, typing.Any]]:
        project_payload = firebase_utils.serialize(ValidateProject(project).get_project_specifics_for_firebase())

        tutorial = TutorialFactory.create(**self.user_resource_kwargs, project=project)
        tutorial_payload = firebase_utils.serialize(ValidateTutorial(tutorial).get_tutorial_specifics_for_firebase())

        return (
            {key: project_payload[key] for key in TILE_SERVER_KEYS if key in project_payload},
            {key: tutorial_payload[key] for key in TILE_SERVER_KEYS if key in tutorial_payload},
        )

    def test_post_event_only(self):
        project = self._create_project()

        for payload in self._get_tile_servers(project):
            # NOTE: Same payload as before pre-event imagery was supported
            assert list(payload.keys()) == ["tileServer"]
            assert payload["tileServer"] == POST_EVENT_TILE_SERVER

    def test_pre_and_post_event(self):
        project = self._create_project(pre_event_tile_server_property=PRE_EVENT_TILE_SERVER_PROPERTY)

        for payload in self._get_tile_servers(project):
            assert payload["tileServer"] == FALLBACK_TILE_SERVER
            assert payload["postEventTileServer"] == POST_EVENT_TILE_SERVER
            assert payload["preEventTileServer"] == PRE_EVENT_TILE_SERVER

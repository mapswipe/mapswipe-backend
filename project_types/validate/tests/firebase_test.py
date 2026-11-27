import typing

import pydantic
import pytest
from pyfirebase_mapswipe import utils as firebase_utils

from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.project.models import Project, ProjectTypeEnum
from apps.tutorial.factories import TutorialFactory
from apps.user.factories import UserFactory
from main.tests import TestCase
from project_types.validate.project import VALIDATE_FALLBACK_RASTER_LAYER, ValidateProject, ValidateProjectProperty
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

TILE_SERVER_KEYS = ("hasPreImagery", "tileServer", "preEventTileServer", "postEventTileServer")


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
            # NOTE: Same tile server as before pre-event imagery was supported
            assert list(payload.keys()) == ["hasPreImagery", "tileServer"]
            assert payload["hasPreImagery"] is False
            assert payload["tileServer"] == POST_EVENT_TILE_SERVER

    def test_pre_and_post_event(self):
        project = self._create_project(
            has_pre_imagery=True,
            pre_event_tile_server_property=PRE_EVENT_TILE_SERVER_PROPERTY,
        )

        for payload in self._get_tile_servers(project):
            assert payload["hasPreImagery"] is True
            assert payload["tileServer"] == FALLBACK_TILE_SERVER
            assert payload["postEventTileServer"] == POST_EVENT_TILE_SERVER
            assert payload["preEventTileServer"] == PRE_EVENT_TILE_SERVER

    def test_pre_event_imagery_set_without_has_pre_imagery(self):
        # NOTE: Stale pre-event imagery left by the form is ignored when has_pre_imagery is False
        project = self._create_project(
            has_pre_imagery=False,
            pre_event_tile_server_property=PRE_EVENT_TILE_SERVER_PROPERTY,
        )

        for payload in self._get_tile_servers(project):
            assert list(payload.keys()) == ["hasPreImagery", "tileServer"]
            assert payload["hasPreImagery"] is False
            assert payload["tileServer"] == POST_EVENT_TILE_SERVER

    def test_zoom_range_of_named_server(self):
        project = self._create_project(
            tile_server_property={"name": "BING", "bing": {"credits": "Bing credits", "min_zoom": 1, "max_zoom": 19}},
            has_pre_imagery=True,
            pre_event_tile_server_property={"name": "ESRI", "esri": {"credits": "ESRI credits", "max_zoom": 17}},
        )

        for payload in self._get_tile_servers(project):
            assert payload["postEventTileServer"]["minZoom"] == 1
            assert payload["postEventTileServer"]["maxZoom"] == 19
            assert "minZoom" not in payload["preEventTileServer"]
            assert payload["preEventTileServer"]["maxZoom"] == 17
            # NOTE: No server defines a zoom range for the fallback image
            assert "minZoom" not in payload["tileServer"]
            assert "maxZoom" not in payload["tileServer"]

    def test_named_server_without_zoom_range(self):
        # NOTE: The default zoom range of a named server is not written
        project = self._create_project(
            tile_server_property={"name": "BING", "bing": {"credits": "Bing credits"}},
            has_pre_imagery=True,
            pre_event_tile_server_property={"name": "ESRI", "esri": {"credits": "ESRI credits"}},
        )

        for payload in self._get_tile_servers(project):
            for key in ["tileServer", "preEventTileServer", "postEventTileServer"]:
                assert "minZoom" not in payload[key]
                assert "maxZoom" not in payload[key]

    def test_zoom_range_of_custom_server(self):
        project = self._create_project(
            tile_server_property={
                "name": "CUSTOM",
                "custom": {
                    "credits": "Post-event credits",
                    "url": "https://post-event.example.com/{z}/{x}/{y}.png",
                    "min_zoom": 2,
                    "max_zoom": 18,
                },
            },
            has_pre_imagery=True,
            pre_event_tile_server_property={
                "name": "CUSTOM",
                "custom": {
                    "credits": "Pre-event credits",
                    "url": "https://pre-event.example.com/{z}/{x}/{y}.png",
                    "max_zoom": 17,
                },
            },
        )

        for payload in self._get_tile_servers(project):
            assert payload["postEventTileServer"] == {**POST_EVENT_TILE_SERVER, "minZoom": 2, "maxZoom": 18}
            assert payload["preEventTileServer"] == {**PRE_EVENT_TILE_SERVER, "maxZoom": 17}

    def test_zoom_range_of_post_event_only(self):
        project = self._create_project(
            tile_server_property={
                "name": "CUSTOM",
                "custom": {
                    "credits": "Post-event credits",
                    "url": "https://post-event.example.com/{z}/{x}/{y}.png",
                    "min_zoom": 2,
                    "max_zoom": 18,
                },
            },
        )

        for payload in self._get_tile_servers(project):
            assert payload["tileServer"] == {**POST_EVENT_TILE_SERVER, "minZoom": 2, "maxZoom": 18}


class TestValidateProjectProperty(TestCase):
    PROJECT_PROPERTY: typing.ClassVar[dict[str, typing.Any]] = {
        "object_source": {
            "source_type": "TASKING_MANAGER",
            "tasking_manager_project_id": "1234",
            "ohsome_filter": "building=*",
        },
        "tile_server_property": POST_EVENT_TILE_SERVER_PROPERTY,
    }

    def test_has_pre_imagery_defaults_to_false(self):
        # NOTE: Existing validate projects do not have has_pre_imagery
        project_property = ValidateProjectProperty.model_validate(self.PROJECT_PROPERTY)
        assert project_property.has_pre_imagery is False
        assert project_property.pre_event_tile_server_property is None

    def test_has_pre_imagery_requires_pre_event_imagery(self):
        with pytest.raises(pydantic.ValidationError, match="Pre-event imagery is required"):
            ValidateProjectProperty.model_validate({**self.PROJECT_PROPERTY, "has_pre_imagery": True})

    def test_pre_event_imagery_dropped_without_has_pre_imagery(self):
        project_property = ValidateProjectProperty.model_validate(
            {
                **self.PROJECT_PROPERTY,
                "has_pre_imagery": False,
                "pre_event_tile_server_property": PRE_EVENT_TILE_SERVER_PROPERTY,
            },
        )
        assert project_property.pre_event_tile_server_property is None

    def test_has_pre_imagery_with_pre_event_imagery(self):
        project_property = ValidateProjectProperty.model_validate(
            {
                **self.PROJECT_PROPERTY,
                "has_pre_imagery": True,
                "pre_event_tile_server_property": PRE_EVENT_TILE_SERVER_PROPERTY,
            },
        )
        assert project_property.pre_event_tile_server_property is not None

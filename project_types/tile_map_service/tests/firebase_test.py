import typing

from pyfirebase_mapswipe import utils as firebase_utils

from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.project.models import Project, ProjectTypeEnum
from apps.user.factories import UserFactory
from main.tests import TestCase
from project_types.tile_map_service.compare.project import CompareProject
from project_types.tile_map_service.find.project import FindProject
from project_types.tile_map_service.locate.project import LocateProject

# NOTE: Both servers have a saved zoom range, which must still not be written
NAMED_TILE_SERVER_PROPERTY = {
    "name": "BING",
    "bing": {
        "credits": "Bing credits",
        "min_zoom": 1,
        "max_zoom": 19,
    },
}
CUSTOM_TILE_SERVER_PROPERTY = {
    "name": "CUSTOM",
    "custom": {
        "credits": "Custom credits",
        "url": "https://custom.example.com/{z}/{x}/{y}.png",
        "min_zoom": 2,
        "max_zoom": 18,
    },
}


class TestTileMapServiceFirebaseTileServers(TestCase):
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

    def _create_project(self, project_type: ProjectTypeEnum, **extra_project_type_specifics: typing.Any) -> Project:
        return ProjectFactory.create(
            **self.user_resource_kwargs,
            requesting_organization=self.organization,
            project_type=project_type,
            project_type_specifics={
                "zoom_level": 18,
                "aoi_geometry": "1",
                **extra_project_type_specifics,
            },
        )

    def _assert_no_zoom_range(self, payload: dict[str, typing.Any], tile_server_keys: list[str]):
        for key in tile_server_keys:
            assert "minZoom" not in payload[key]
            assert "maxZoom" not in payload[key]

    def test_find_has_no_zoom_range(self):
        for tile_server_property in [NAMED_TILE_SERVER_PROPERTY, CUSTOM_TILE_SERVER_PROPERTY]:
            project = self._create_project(ProjectTypeEnum.FIND, tile_server_property=tile_server_property)
            payload = firebase_utils.serialize(FindProject(project).get_project_specifics_for_firebase())
            self._assert_no_zoom_range(payload, ["tileServer"])

    def test_compare_has_no_zoom_range(self):
        project = self._create_project(
            ProjectTypeEnum.COMPARE,
            tile_server_property=NAMED_TILE_SERVER_PROPERTY,
            tile_server_b_property=CUSTOM_TILE_SERVER_PROPERTY,
        )
        payload = firebase_utils.serialize(CompareProject(project).get_project_specifics_for_firebase())
        self._assert_no_zoom_range(payload, ["tileServer", "tileServerB"])

    def test_locate_has_no_zoom_range(self):
        for tile_server_property in [NAMED_TILE_SERVER_PROPERTY, CUSTOM_TILE_SERVER_PROPERTY]:
            project = self._create_project(
                ProjectTypeEnum.LOCATE,
                tile_server_property=tile_server_property,
                sub_grid_size="2x2",
                export_meta_key="building",
                export_meta_value="roof_top",
            )
            payload = firebase_utils.serialize(LocateProject(project).get_project_specifics_for_firebase())
            self._assert_no_zoom_range(payload, ["tileServer"])

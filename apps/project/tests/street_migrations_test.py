import copy
import importlib
import typing

from django.apps import apps

from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.project.models import Project, ProjectTypeEnum
from apps.user.factories import UserFactory
from main.tests import TestCase
from project_types.street.project import StreetProjectProperty

backfill_provider = importlib.import_module(
    "apps.project.migrations.0013_backfill_image_provider_for_street_projects",
).backfill_provider
migrate_is_pano_to_pano_only = importlib.import_module(
    "apps.project.migrations.0014_migrate_pano_only_for_street_projects",
).migrate_is_pano_to_pano_only
migrate_sampling_threshold_to_meters = importlib.import_module(
    "apps.project.migrations.0016_migrate_sampling_threshold_to_meters_for_street_projects",
).migrate_sampling_threshold_to_meters


def with_types(value: typing.Any) -> typing.Any:
    # NOTE: `==` treats 100 and 100.0 (and 1 and True) as equal
    if isinstance(value, dict):
        return {key: with_types(item) for key, item in value.items()}
    if isinstance(value, list):
        return [with_types(item) for item in value]
    return (type(value), value)


class TestStreetMigrations(TestCase):
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

    def create_project(
        self,
        project_type_specifics: typing.Any,
        project_type: ProjectTypeEnum = ProjectTypeEnum.STREET,
    ) -> Project:
        return ProjectFactory.create(
            **self.user_resource_kwargs,
            requesting_organization=self.organization,
            project_type=project_type,
            project_type_specifics=project_type_specifics,
        )

    def assert_migration(
        self,
        migration: typing.Callable[..., None],
        cases: list[tuple[typing.Any, typing.Any]],
    ) -> list[Project]:
        projects = [(self.create_project(before), after) for before, after in cases]
        non_street_filters = {"is_pano": True, "sampling_threshold": 0.5}
        non_street_specifics = {"mapillary_image_filters": non_street_filters, "mapillary": non_street_filters}
        non_street_project = self.create_project(copy.deepcopy(non_street_specifics), project_type=ProjectTypeEnum.FIND)

        migration(apps, None)

        for project, expected in projects:
            project.refresh_from_db()
            assert with_types(project.project_type_specifics) == with_types(expected), (project.pk, expected)
        non_street_project.refresh_from_db()
        assert with_types(non_street_project.project_type_specifics) == with_types(non_street_specifics)
        return [project for project, _ in projects]

    def test_backfill_provider(self):
        self.assert_migration(
            backfill_provider,
            [
                ({"aoi_geometry": "1"}, {"aoi_geometry": "1", "provider": "mapillary"}),
                (
                    {"aoi_geometry": "1", "mapillary_image_filters": {"is_pano": True, "organization_id": "42"}},
                    {"aoi_geometry": "1", "provider": "mapillary", "mapillary": {"is_pano": True, "organization_id": "42"}},
                ),
                ({"provider": "panoramax", "panoramax": {}}, {"provider": "panoramax", "panoramax": {}}),
                (None, None),
            ],
        )

    def test_migrate_is_pano_to_pano_only(self):
        self.assert_migration(
            migrate_is_pano_to_pano_only,
            [
                ({"mapillary": {"is_pano": True}}, {"mapillary": {"pano_only": True}}),
                (
                    {"mapillary": {"is_pano": False, "pano_only": True}},
                    {"mapillary": {"pano_only": True}},
                ),
            ],
        )

    def test_migrate_sampling_threshold_to_meters(self):
        cases = [
            (0.1, {"sampling_threshold": 100}),
            (1.0, {"sampling_threshold": 1000}),
            (2, {"sampling_threshold": 2000}),
            (0.0004, {}),
            (0.0, {}),
            (-0.1, {}),
            (None, {"sampling_threshold": None}),
            (True, {"sampling_threshold": True}),
        ]
        self.assert_migration(
            migrate_sampling_threshold_to_meters,
            [
                (
                    {"mapillary": {"sampling_threshold": sampling_threshold_km}},
                    {"mapillary": expected_filters},
                )
                for sampling_threshold_km, expected_filters in cases
            ],
        )

    def test_migrate_develop_street_project(self):
        def migrate(*args: typing.Any):
            backfill_provider(*args)
            migrate_is_pano_to_pano_only(*args)
            migrate_sampling_threshold_to_meters(*args)

        [project] = self.assert_migration(
            migrate,
            [
                (
                    {
                        "aoi_geometry": "1",
                        "custom_options": [],
                        "mapillary_image_filters": {
                            "is_pano": True,
                            "organization_id": "42",
                            "randomize_order": False,
                            "sampling_threshold": 0.1,
                        },
                    },
                    {
                        "provider": "mapillary",
                        "aoi_geometry": "1",
                        "custom_options": [],
                        "mapillary": {
                            "pano_only": True,
                            "organization_id": "42",
                            "randomize_order": False,
                            "sampling_threshold": 100,
                        },
                    },
                ),
            ],
        )
        StreetProjectProperty.model_validate(project.project_type_specifics)

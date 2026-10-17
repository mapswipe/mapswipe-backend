import copy
import importlib
import typing

from django.apps import apps

from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.project.models import Project, ProjectTypeEnum
from apps.user.factories import UserFactory
from main.tests import TestCase

backfill_image_provider = importlib.import_module(
    "apps.project.migrations.0013_backfill_image_provider_for_street_projects",
).backfill_image_provider
migrate_is_pano_to_pano_only = importlib.import_module(
    "apps.project.migrations.0014_migrate_pano_only_for_street_projects",
).migrate_is_pano_to_pano_only
migrate_sampling_threshold_to_meters = importlib.import_module(
    "apps.project.migrations.0016_migrate_sampling_threshold_to_meters_for_street_projects",
).migrate_sampling_threshold_to_meters


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
    ):
        projects = [(self.create_project(before), after) for before, after in cases]
        non_street_specifics = {"mapillary_image_filters": {"is_pano": True, "sampling_threshold": 0.5}}
        non_street_project = self.create_project(copy.deepcopy(non_street_specifics), project_type=ProjectTypeEnum.FIND)

        migration(apps, None)

        for project, expected in projects:
            project.refresh_from_db()
            assert project.project_type_specifics == expected, (project.pk, expected)
        non_street_project.refresh_from_db()
        assert non_street_project.project_type_specifics == non_street_specifics

    def test_backfill_image_provider(self):
        self.assert_migration(
            backfill_image_provider,
            [
                ({"aoi_geometry": "1"}, {"aoi_geometry": "1", "image_provider": {"name": "mapillary"}}),
                ({"image_provider": {"name": "panoramax"}}, {"image_provider": {"name": "panoramax"}}),
                (None, None),
            ],
        )

    def test_migrate_is_pano_to_pano_only(self):
        self.assert_migration(
            migrate_is_pano_to_pano_only,
            [
                ({"mapillary_image_filters": {"is_pano": True}}, {"mapillary_image_filters": {"pano_only": True}}),
                (
                    {"mapillary_image_filters": {"is_pano": False, "pano_only": True}},
                    {"mapillary_image_filters": {"pano_only": True}},
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
        ]
        self.assert_migration(
            migrate_sampling_threshold_to_meters,
            [
                (
                    {"mapillary_image_filters": {"sampling_threshold": sampling_threshold_km}},
                    {"mapillary_image_filters": expected_filters},
                )
                for sampling_threshold_km, expected_filters in cases
            ],
        )

import datetime
import typing

from django.contrib.gis.geos import Point

from apps.contributor.factories import ContributorUserFactory
from apps.mapping.factories import (
    MappingSessionFactory,
    MappingSessionResultFactory,
)
from apps.project.exports.exports import export_project_data
from apps.project.factories import OrganizationFactory, ProjectFactory, ProjectTaskFactory, ProjectTaskGroupFactory
from apps.project.models import ProjectAsset, ProjectStatusEnum, ProjectTypeEnum
from apps.user.factories import UserFactory
from main.tests import TestCase
from project_types.tile_map_service.find.project import (
    FindProjectProperty,
    FindProjectTaskGroupProperty,
    FindProjectTaskProperty,
)
from utils.geo.raster_tile_server.config import RasterTileServerNameEnum
from utils.geo.raster_tile_server.models import RasterTileServerCommonConfig, RasterTileServerConfig


class TestProjectExport(TestCase):
    @typing.override
    @classmethod
    def setUpClass(cls):
        # TODO: this is almost copy of apps/community_dashboard/tests/query_test.py

        super().setUpClass()
        cls.user = UserFactory.create()
        cls.user_resource_kwargs = dict(
            created_by=cls.user,
            modified_by=cls.user,
        )

        cls.organization1 = OrganizationFactory.create(**cls.user_resource_kwargs)

        cls.project = ProjectFactory.create(
            **cls.user_resource_kwargs,
            topic="Find Project Alpha",
            requesting_organization=cls.organization1,
            project_type=ProjectTypeEnum.FIND,
            status=ProjectStatusEnum.PUBLISHED,
            project_type_specifics=FindProjectProperty(
                zoom_level=14,
                tile_server_property=RasterTileServerConfig(
                    name=RasterTileServerNameEnum.BING,
                    bing=RasterTileServerCommonConfig(credits="Looks good"),
                ),
                aoi_geometry="1234",
            ).model_dump(),
        )
        cls.project_groups = ProjectTaskGroupFactory.create_batch(
            4,
            project=cls.project,
            project_type_specifics=FindProjectTaskGroupProperty(
                x_min=1,
                x_max=5,
                y_min=1,
                y_max=5,
            ).model_dump(),
        )
        cls.project_tasks = [
            _task
            for _group in cls.project_groups
            for _task in ProjectTaskFactory.create_batch(
                4,
                task_group=_group,
                geometry=Point(1, 2),
                project_type_specifics=FindProjectTaskProperty(
                    tile_x=1,
                    tile_y=2,
                ).model_dump(),
            )
        ]

        cls.now = datetime.datetime(
            year=2025,
            month=5,
            day=9,
            tzinfo=datetime.UTC,
        )
        base_datetime = cls.now - datetime.timedelta(days=1)
        old_mapping_session_datetime = base_datetime - datetime.timedelta(days=40)

        cls.contributor_users = ContributorUserFactory.create_batch(10)

        cls.mapping_sessions = {
            (contributor_user.pk, _project_group.pk): MappingSessionFactory.create(
                project_task_group=_project_group,
                contributor_user=contributor_user,
                start_time=_base_datetime,
                end_time=_base_datetime + datetime.timedelta(minutes=1),
                items_count=10,
            )
            for _contributor_users, _base_datetime in [
                (cls.contributor_users[:5], old_mapping_session_datetime),
                (cls.contributor_users[5:], base_datetime),
            ]
            for _project_group in cls.project_groups
            for contributor_user in _contributor_users
        }

        cls.results = {
            (contributor_user.pk, _value): [
                MappingSessionResultFactory.create(
                    session=cls.mapping_sessions.get((contributor_user.pk, _project_task.task_group_id)),
                    project_task_id=_project_task.pk,
                    result=_value,
                )
                for _project_task in cls.project_tasks
            ]
            for _value, contributor_users in [
                (0, cls.contributor_users[:4]),
                (1, cls.contributor_users[4:]),
            ]
            for contributor_user in contributor_users
        }

    def test_filter_by_id(self):
        assert ProjectAsset.objects.count() == 0
        export_project_data(self.project)
        new_project_assets_01 = {project_asset.pk: project_asset.file.name for project_asset in ProjectAsset.objects.all()}
        export_project_data(self.project)

        new_project_assets_02 = {project_asset.pk: project_asset.file.name for project_asset in ProjectAsset.objects.all()}

        # Exports name should't change on re-generate
        assert new_project_assets_02 == new_project_assets_01

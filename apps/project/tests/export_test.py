import datetime
import typing

import pytest
from django.contrib.gis.geos import Point

from apps.common.models import GlobalExportAsset
from apps.contributor.factories import ContributorUserFactory
from apps.mapping.factories import (
    MappingSessionFactory,
    MappingSessionResultFactory,
)
from apps.project.exports.exports import export_project_data
from apps.project.factories import (
    OrganizationFactory,
    ProjectAssetFactory,
    ProjectFactory,
    ProjectTaskFactory,
    ProjectTaskGroupFactory,
)
from apps.project.models import ProjectAsset, ProjectStatusEnum, ProjectTypeEnum
from apps.project.tasks import regenerate_global_project_assets
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

        # Dummy projects
        ProjectFactory.create_batch(
            5,
            **cls.user_resource_kwargs,
            requesting_organization=cls.organization1,
            project_type=ProjectTypeEnum.FIND,
        )
        ProjectFactory.create_batch(
            2,
            **cls.user_resource_kwargs,
            requesting_organization=cls.organization1,
            project_type=ProjectTypeEnum.VALIDATE,
        )

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
                    url="https://some-service.com/14/1/2/",
                ).model_dump(),
            )
        ]
        cls.project_image = ProjectAssetFactory.generate_image_asset(project=cls.project, **cls.user_resource_kwargs)
        cls.project.image = cls.project_image
        cls.project.save()

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

    def test_exports(self):
        assert ProjectAsset.objects.count() == 1
        export_project_data(self.project)

        new_project_assets_01 = {project_asset.pk: project_asset.file.name for project_asset in ProjectAsset.objects.all()}
        export_project_data(self.project)

        new_project_assets_02 = {project_asset.pk: project_asset.file.name for project_asset in ProjectAsset.objects.all()}

        # Exports name should't change on re-generate
        assert new_project_assets_02 == new_project_assets_01

    def test_project_stats(self):
        project = self.project

        def _get_data():
            project.refresh_from_db()
            return {
                "progress": project.progress,
                "number_of_contributor_users": project.number_of_contributor_users,
                "number_of_results": project.number_of_results,
                "number_of_results_for_progress": project.number_of_results_for_progress,
                "last_contribution_date": project.last_contribution_date,
            }

        assert _get_data() == {
            "progress": 0,
            "number_of_contributor_users": 0,
            "number_of_results": 0,
            "number_of_results_for_progress": 0,
            "last_contribution_date": None,
        }

        export_project_data(self.project)

        assert _get_data() == {
            "progress": 10,
            "number_of_contributor_users": 10,
            "number_of_results": 4000,
            "number_of_results_for_progress": 4000,
            "last_contribution_date": datetime.date(2025, 5, 8),
        }

    def test_project_overall_global_assets(self):
        # TODO: Add file content match
        assert GlobalExportAsset.objects.count() == 0
        export_project_data(self.project)
        regenerate_global_project_assets()
        assert GlobalExportAsset.objects.count() == 4

        # XXX: To look at the preview
        # for a in GlobalExportAsset.objects.all():
        #     print(a.type_enum.label, "#" * 22)
        #     print(a.file.read().decode("utf-8"))
        #     print("-" * 22)
        # assert False

        assert [
            {
                "type": a.type_enum.label,
                "file_name": a.file.name,
                "file_size": pytest.approx(a.file.size, rel=0.1),
            }
            for a in GlobalExportAsset.objects.all()
        ] == [
            {
                "type": "All projects",
                "file_name": "global/asset/projects.csv",
                "file_size": 2099,
            },
            {
                "type": "Projects geojson with centroid",
                "file_name": "global/asset/projects_centroid.geojson",
                "file_size": 5350,
            },
            {
                "file_name": "global/asset/projects_geom.geojson",
                "type": "Projects Geojson with GEOM",
                "file_size": 5350,
            },
            {
                "type": "Project Type Aggregates",
                "file_name": "global/asset/project_stats_by_types.csv",
                "file_size": 236,
            },
        ]

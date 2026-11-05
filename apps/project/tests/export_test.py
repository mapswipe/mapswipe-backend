import datetime
import typing
from unittest import mock

import pytest
import sentry_sdk
from django.contrib.gis.geos import Point
from django.test import override_settings
from django.utils import timezone

from apps.common.models import AssetTypeEnum, GlobalExportAsset
from apps.contributor.factories import ContributorUserFactory
from apps.mapping.factories import (
    MappingSessionFactory,
    MappingSessionResultFactory,
)
from apps.project.exports.exports import SHORT_TERM_EXPORT_DEMOTED_FINGERPRINT, export_project_data
from apps.project.factories import (
    OrganizationFactory,
    ProjectAssetFactory,
    ProjectFactory,
    ProjectTaskFactory,
    ProjectTaskGroupFactory,
)
from apps.project.models import ProjectAsset, ProjectAssetExportTypeEnum, ProjectStatusEnum, ProjectTypeEnum
from apps.project.tasks import regenerate_global_project_assets
from apps.user.factories import UserFactory
from main.config import Config
from main.sentry import SentryTag, capture_grouped_error
from main.tests import TestCase
from project_types.tile_map_service.find.project import (
    FindProjectProperty,
    FindProjectTaskGroupProperty,
    FindProjectTaskProperty,
)
from utils.geo.raster_tile_server.config import RasterTileServerNameEnum
from utils.geo.raster_tile_server.models import RasterTileServerCommonConfig, RasterTileServerConfig


class TestProjectExport(TestCase):
    class Query:
        PUBLIC_PROJECT_EXPORT = """
            query PublicProjectExport($pk: ID!) {
                publicProject(id: $pk) {
                    exportResults {
                        file {
                            name
                            url
                        }
                    }
                }
            }
        """

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
            verification_number=3,
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

    def get_export_assets(self):
        return ProjectAsset.objects.filter(project=self.project, type=AssetTypeEnum.EXPORT)

    @override_settings(SHORT_TERM_STORAGE_ENABLED=False)
    def test_exports_without_short_term_storage(self):
        export_project_data(self.project)

        export_assets = list(self.get_export_assets())
        assert len(export_assets) > 0
        for project_asset in export_assets:
            assert project_asset.file
            assert project_asset.file.storage.exists(project_asset.file.name)
            assert not project_asset.short_term_file
            assert project_asset.current_file == project_asset.file

    @override_settings(SHORT_TERM_STORAGE_ENABLED=True)
    def test_exports_with_short_term_storage(self):
        export_project_data(self.project)

        export_assets = list(self.get_export_assets())
        assert len(export_assets) > 0
        for project_asset in export_assets:
            assert not project_asset.file
            assert project_asset.short_term_file
            assert project_asset.short_term_file.storage.exists(project_asset.short_term_file.name)
            assert project_asset.current_file == project_asset.short_term_file
            assert project_asset.file_size == project_asset.short_term_file.size
            assert project_asset.mimetype == ProjectAssetExportTypeEnum.get_mimetype(
                ProjectAssetExportTypeEnum(project_asset.export_type),
            )

        results_asset = self.get_export_assets().get(export_type=ProjectAssetExportTypeEnum.RESULTS)
        file_name = results_asset.short_term_file.name

        def _query_export_results_file():
            content = self.query_check(self.Query.PUBLIC_PROJECT_EXPORT, variables={"pk": self.gID(self.project.pk)})
            return content["data"]["publicProject"]["exportResults"]["file"]

        media_domain = Config.MEDIA_STORAGE_DOMAIN.geturl()

        # Short-term file
        assert _query_export_results_file() == {
            "name": file_name,
            "url": f"{media_domain}/short-term/{file_name}",
        }

        # Long-term file (promoted)
        results_asset.file.name = file_name
        results_asset.promoted_at = timezone.now()
        results_asset.save(update_fields=("file", "promoted_at"))
        assert _query_export_results_file() == {
            "name": file_name,
            "url": f"{media_domain}/media/{file_name}",
        }

    @override_settings(SHORT_TERM_STORAGE_ENABLED=True)
    def test_exports_demote_promoted_asset(self):
        export_project_data(self.project)

        # Promote one export asset
        results_asset = self.get_export_assets().get(export_type=ProjectAssetExportTypeEnum.RESULTS)
        file_name = results_asset.short_term_file.name
        results_asset.file.name = file_name
        results_asset.promoted_at = timezone.now()
        results_asset.save(update_fields=("file", "promoted_at"))
        results_asset.short_term_file.delete(save=True)

        with mock.patch("apps.project.exports.exports.capture_grouped_error") as capture_grouped_error_mock:
            export_project_data(self.project)

        results_asset.refresh_from_db()
        assert not results_asset.file
        assert results_asset.promoted_at is None
        assert results_asset.short_term_file.name == file_name
        assert results_asset.short_term_file.storage.exists(file_name)

        capture_grouped_error_mock.assert_called_once()
        assert capture_grouped_error_mock.call_args.kwargs["fingerprint"] == [SHORT_TERM_EXPORT_DEMOTED_FINGERPRINT]
        assert capture_grouped_error_mock.call_args.kwargs["tags"] == {SentryTag.Tag.PROJECT: self.project.pk}
        assert capture_grouped_error_mock.call_args.kwargs["extra"] == {
            "project_id": self.project.pk,
            "export_type": ProjectAssetExportTypeEnum.RESULTS.name,
        }

        # Other export assets are not demoted
        assert not self.get_export_assets().filter(file__isnull=False).exists()

    def test_capture_grouped_error(self):
        captured_scopes = []

        def _capture_message(message: str, level: str):
            scope = sentry_sdk.get_current_scope()
            captured_scopes.append(
                {
                    "message": message,
                    "level": level,
                    "fingerprint": scope._fingerprint,  # type: ignore[reportPrivateUsage]
                    "tags": scope._tags,  # type: ignore[reportPrivateUsage]
                    "extras": scope._extras,  # type: ignore[reportPrivateUsage]
                },
            )

        with mock.patch("main.sentry.sentry_sdk.capture_message", side_effect=_capture_message):
            capture_grouped_error(
                "Something failed",
                fingerprint=["some-fingerprint"],
                tags={SentryTag.Tag.PROJECT: 1},
                extra={"export_type": "RESULTS"},
            )

        assert captured_scopes == [
            {
                "message": "Something failed",
                "level": "error",
                "fingerprint": ["some-fingerprint"],
                "tags": {SentryTag.Tag.PROJECT.value: 1},
                "extras": {"export_type": "RESULTS"},
            },
        ]
        # The scope is not changed outside of capture_grouped_error
        assert sentry_sdk.get_current_scope()._fingerprint is None  # type: ignore[reportPrivateUsage]

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
            "progress": 100,
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

import contextlib
import datetime
import typing
from io import StringIO
from unittest import mock

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone
from ulid import ULID

from apps.common.models import AssetTypeEnum, FirebasePushStatusEnum
from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.project.models import Project, ProjectAsset, ProjectAssetExportTypeEnum, ProjectStatusEnum
from apps.project.short_term_storage import SHORT_TERM_PROMOTION_FAILED_FINGERPRINT, promote_and_cleanup
from apps.project.tasks import promote_and_cleanup_short_term_storage
from apps.tutorial.factories import TutorialFactory
from apps.tutorial.models import Tutorial, TutorialStatusEnum
from apps.user.factories import UserFactory
from main.cache import CeleryLock, cache
from main.config import Config
from main.sentry import SentryTag
from main.storage_backends import FileSystemStorage
from main.tests import TestCase

EXPORT_TYPES = (ProjectAssetExportTypeEnum.RESULTS, ProjectAssetExportTypeEnum.AGGREGATED_RESULTS)


@override_settings(
    SHORT_TERM_STORAGE_ENABLED=True,
    SHORT_TERM_STORAGE_PROMOTION_COOLDOWN_DAYS=7,
    SHORT_TERM_STORAGE_TTL_DAYS=7,
)
class TestShortTermStoragePromotion(TestCase):
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
        super().setUpClass()
        cls.user = UserFactory.create()
        cls.user_resource_kwargs = dict(created_by=cls.user, modified_by=cls.user)
        cls.organization = OrganizationFactory.create(**cls.user_resource_kwargs)

    @typing.override
    def setUp(self):
        super().setUp()
        self.now = timezone.now()  # type: ignore[reportUninitializedInstanceVariable]
        self.stale_at = self.now - datetime.timedelta(days=8)  # type: ignore[reportUninitializedInstanceVariable]

    def create_project(self, status: ProjectStatusEnum) -> Project:
        return ProjectFactory.create(
            **self.user_resource_kwargs,
            requesting_organization=self.organization,
            status=status,
        )

    def create_export_assets(self, project: Project, *, modified_at: datetime.datetime | None = None):
        project_assets = [
            ProjectAsset.objects.create(
                **self.user_resource_kwargs,
                client_id=str(ULID()),
                project=project,
                type=AssetTypeEnum.EXPORT,
                export_type=export_type,
                mimetype=ProjectAssetExportTypeEnum.get_mimetype(export_type),
                file_size=len(self.get_content(project, export_type)),
                short_term_file=ContentFile(self.get_content(project, export_type), name=f"{export_type.name}.csv"),
            )
            for export_type in EXPORT_TYPES
        ]
        ProjectAsset.objects.filter(pk__in=[asset.pk for asset in project_assets]).update(
            modified_at=modified_at or self.stale_at,
        )
        return project_assets

    def get_content(self, project: Project, export_type: ProjectAssetExportTypeEnum) -> bytes:
        return f"project-{project.pk}-{export_type.name}".encode()

    def get_export_assets(self, project: Project):
        return list(ProjectAsset.objects.filter(project=project, type=AssetTypeEnum.EXPORT).order_by("id"))

    def snapshot(self, project: Project):
        return [
            (asset.file.name, asset.short_term_file.name, asset.promoted_at, asset.modified_at)
            for asset in self.get_export_assets(project)
        ]

    def test_promote(self):
        finished_project = self.create_project(ProjectStatusEnum.FINISHED)
        withdrawn_project = self.create_project(ProjectStatusEnum.WITHDRAWN)
        published_project = self.create_project(ProjectStatusEnum.PUBLISHED)
        for project in [finished_project, withdrawn_project, published_project]:
            self.create_export_assets(project)
        published_snapshot = self.snapshot(published_project)

        summary = promote_and_cleanup()

        assert (summary.promoted, summary.skipped_cooldown, summary.skipped_locked, summary.failed) == (2, 0, 0, 0)
        for project in [finished_project, withdrawn_project]:
            for asset in self.get_export_assets(project):
                assert asset.file.name == asset.short_term_file.name
                assert asset.file.storage.exists(asset.file.name)
                assert asset.short_term_file.storage.exists(asset.short_term_file.name)
                assert asset.file.storage is not asset.short_term_file.storage
                with asset.file.open("rb") as fp:
                    assert fp.read() == self.get_content(project, ProjectAssetExportTypeEnum(asset.export_type))
                assert asset.promoted_at is not None
                assert asset.promoted_at >= self.now
                # modified_at is not changed by promotion
                assert asset.modified_at == self.stale_at

        assert self.snapshot(published_project) == published_snapshot

        # Already promoted assets are not promoted again
        summary = promote_and_cleanup()
        assert (summary.promoted, summary.skipped_cooldown, summary.failed) == (0, 0, 0)

    def test_promote_skips_project_in_cooldown(self):
        project = self.create_project(ProjectStatusEnum.FINISHED)
        project_assets = self.create_export_assets(project)
        # One recently modified export asset holds back the whole project
        ProjectAsset.objects.filter(pk=project_assets[0].pk).update(modified_at=self.now - datetime.timedelta(days=1))
        snapshot = self.snapshot(project)

        summary = promote_and_cleanup()

        assert (summary.promoted, summary.skipped_cooldown) == (0, 1)
        assert self.snapshot(project) == snapshot

    def test_promote_cooldown_boundary(self):
        # The cooldown is shortened by SCHEDULE_GRACE
        promoted_project = self.create_project(ProjectStatusEnum.FINISHED)
        self.create_export_assets(promoted_project, modified_at=self.now - datetime.timedelta(days=7, hours=-11))
        cooldown_project = self.create_project(ProjectStatusEnum.FINISHED)
        self.create_export_assets(cooldown_project, modified_at=self.now - datetime.timedelta(days=7, hours=-13))

        summary = promote_and_cleanup()

        assert (summary.promoted, summary.skipped_cooldown) == (1, 1)
        assert all(asset.file for asset in self.get_export_assets(promoted_project))
        assert not any(asset.file for asset in self.get_export_assets(cooldown_project))

    def test_project_lock_expire(self):
        project = self.create_project(ProjectStatusEnum.FINISHED)
        self.create_export_assets(project)
        project_lock_id = CeleryLock.Key.PROJECT_EXPORTS_GENERATE.format(project.pk)
        lock_ttls: list[int | None] = []
        original_redis_lock = CeleryLock.redis_lock

        @contextlib.contextmanager
        def _redis_lock(lock_id: str, **kwargs: typing.Any):
            with original_redis_lock(lock_id, **kwargs) as acquired:
                if lock_id == project_lock_id:
                    lock_ttls.append(cache.ttl(lock_id))
                yield acquired

        with mock.patch.object(CeleryLock, "redis_lock", _redis_lock):
            # Promote
            promote_and_cleanup()
            ProjectAsset.objects.filter(project=project).update(promoted_at=self.now - datetime.timedelta(days=8))
            # Cleanup
            promote_and_cleanup()

        assert len(lock_ttls) == 2
        assert all(ttl is not None and ttl > settings.DEFAULT_REDIS_LOCK_EXPIRE for ttl in lock_ttls), lock_ttls

    def test_promote_skips_locked_project(self):
        project = self.create_project(ProjectStatusEnum.FINISHED)
        self.create_export_assets(project)
        snapshot = self.snapshot(project)

        with CeleryLock.redis_lock(CeleryLock.Key.PROJECT_EXPORTS_GENERATE.format(project.pk)) as acquired:
            assert acquired
            summary = promote_and_cleanup()
        assert (summary.promoted, summary.skipped_locked) == (0, 1)
        assert self.snapshot(project) == snapshot

        summary = promote_and_cleanup()
        assert (summary.promoted, summary.skipped_locked) == (1, 0)

    def test_promote_failure(self):
        failed_project = self.create_project(ProjectStatusEnum.FINISHED)
        self.create_export_assets(failed_project)
        snapshot = self.snapshot(failed_project)

        original_save = FileSystemStorage.save
        saved_names: list[str] = []

        def _save(storage: FileSystemStorage, name: str, content: typing.Any, max_length: int | None = None):
            saved_names.append(name)
            # Fail after the first export asset is promoted
            if len(saved_names) > 1:
                raise Exception("Failed to save")
            return original_save(storage, name, content, max_length=max_length)

        with (
            mock.patch.object(FileSystemStorage, "save", autospec=True, side_effect=_save),
            mock.patch("apps.project.short_term_storage.capture_grouped_error") as capture_grouped_error_mock,
        ):
            summary = promote_and_cleanup()

        assert (summary.promoted, summary.failed) == (0, 1)
        assert len(saved_names) == 2
        # Rows are unchanged, including the export asset copied before the failure
        assert self.snapshot(failed_project) == snapshot
        assert all(not asset.file for asset in self.get_export_assets(failed_project))

        capture_grouped_error_mock.assert_called_once()
        assert capture_grouped_error_mock.call_args.kwargs["fingerprint"] == [SHORT_TERM_PROMOTION_FAILED_FINGERPRINT]
        assert capture_grouped_error_mock.call_args.kwargs["tags"] == {SentryTag.Tag.PROJECT: failed_project.pk}

        # Retried on the next run
        summary = promote_and_cleanup()
        assert (summary.promoted, summary.failed) == (1, 0)

    def test_cleanup(self):
        expired_project = self.create_project(ProjectStatusEnum.FINISHED)
        recent_project = self.create_project(ProjectStatusEnum.FINISHED)
        for project in [expired_project, recent_project]:
            self.create_export_assets(project)
        promote_and_cleanup()

        ProjectAsset.objects.filter(project=expired_project).update(promoted_at=self.now - datetime.timedelta(days=8))
        ProjectAsset.objects.filter(project=recent_project).update(promoted_at=self.now - datetime.timedelta(days=6))
        expired_assets = self.get_export_assets(expired_project)
        recent_snapshot = self.snapshot(recent_project)

        # Not promoted (promoted_at is null) while file is set: never cleaned
        not_promoted_project = self.create_project(ProjectStatusEnum.FINISHED)
        not_promoted_assets = self.create_export_assets(not_promoted_project)
        for asset in not_promoted_assets:
            asset.file.name = asset.short_term_file.name
            asset.save(update_fields=("file",))
        not_promoted_snapshot = self.snapshot(not_promoted_project)

        summary = promote_and_cleanup()

        assert (summary.cleaned, summary.cleanup_skipped_locked, summary.cleanup_failed) == (len(EXPORT_TYPES), 0, 0)
        for old_asset, asset in zip(expired_assets, self.get_export_assets(expired_project), strict=True):
            assert not asset.short_term_file
            assert not old_asset.short_term_file.storage.exists(old_asset.short_term_file.name)
            assert asset.file.name == old_asset.file.name
            assert asset.file.storage.exists(asset.file.name)

        assert self.snapshot(recent_project) == recent_snapshot
        for asset in self.get_export_assets(recent_project):
            assert asset.short_term_file.storage.exists(asset.short_term_file.name)

        assert self.snapshot(not_promoted_project) == not_promoted_snapshot

    def test_cleanup_ttl_boundary(self):
        # The TTL is shortened by SCHEDULE_GRACE
        expired_project = self.create_project(ProjectStatusEnum.FINISHED)
        recent_project = self.create_project(ProjectStatusEnum.FINISHED)
        for project in [expired_project, recent_project]:
            self.create_export_assets(project)
        promote_and_cleanup()
        ProjectAsset.objects.filter(project=expired_project).update(
            promoted_at=self.now - datetime.timedelta(days=7, hours=-11),
        )
        ProjectAsset.objects.filter(project=recent_project).update(
            promoted_at=self.now - datetime.timedelta(days=7, hours=-13),
        )

        summary = promote_and_cleanup()

        assert summary.cleaned == len(EXPORT_TYPES)
        assert not any(asset.short_term_file for asset in self.get_export_assets(expired_project))
        assert all(asset.short_term_file for asset in self.get_export_assets(recent_project))

    @override_settings(SHORT_TERM_STORAGE_ENABLED=False)
    def test_disabled(self):
        project = self.create_project(ProjectStatusEnum.FINISHED)
        self.create_export_assets(project)
        snapshot = self.snapshot(project)

        result = promote_and_cleanup_short_term_storage()

        assert result == {
            "promoted": 0,
            "skipped_cooldown": 0,
            "skipped_locked": 0,
            "failed": 0,
            "cleaned": 0,
            "cleanup_skipped_locked": 0,
            "cleanup_failed": 0,
        }
        assert self.snapshot(project) == snapshot

    def test_graphql_after_promotion(self):
        project = self.create_project(ProjectStatusEnum.FINISHED)
        self.create_export_assets(project)
        results_asset = ProjectAsset.objects.get(project=project, export_type=ProjectAssetExportTypeEnum.RESULTS)
        file_name = results_asset.short_term_file.name
        media_domain = Config.MEDIA_STORAGE_DOMAIN.geturl()

        def _query_export_results_file():
            content = self.query_check(self.PUBLIC_PROJECT_EXPORT, variables={"pk": self.gID(project.pk)})
            return content["data"]["publicProject"]["exportResults"]["file"]

        assert _query_export_results_file() == {"name": file_name, "url": f"{media_domain}/short-term/{file_name}"}
        promote_and_cleanup()
        assert _query_export_results_file() == {"name": file_name, "url": f"{media_domain}/media/{file_name}"}


class TestPushMediaUrlsToFirebaseCommand(TestCase):
    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = UserFactory.create()
        user_resource_kwargs = dict(created_by=user, modified_by=user)
        organization = OrganizationFactory.create(**user_resource_kwargs)
        pushed_at = timezone.now()

        def _create_project(status: ProjectStatusEnum, firebase_last_pushed: datetime.datetime | None = pushed_at):
            project = ProjectFactory.create(
                **user_resource_kwargs,
                requesting_organization=organization,
                status=status,
                firebase_push_status=FirebasePushStatusEnum.SUCCESS,
                firebase_last_pushed=firebase_last_pushed,
            )
            tutorial = TutorialFactory.create(
                **user_resource_kwargs,
                project=project,
                name=f"Tutorial {project.pk}",
                status=TutorialStatusEnum.PUBLISHED,
                firebase_push_status=FirebasePushStatusEnum.SUCCESS,
                firebase_last_pushed=pushed_at,
            )
            project.tutorial = tutorial
            project.save(update_fields=("tutorial",))
            return project

        cls.published_project = _create_project(ProjectStatusEnum.PUBLISHED)
        cls.paused_project = _create_project(ProjectStatusEnum.PAUSED)
        cls.finished_project = _create_project(ProjectStatusEnum.FINISHED)
        cls.not_pushed_project = _create_project(ProjectStatusEnum.PUBLISHED, firebase_last_pushed=None)

    def call_command(self, *args: str) -> str:
        out = StringIO()
        call_command("push_media_urls_to_firebase", *args, stdout=out, stderr=StringIO())
        return out.getvalue()

    def mock_push(self, model: type[Project | Tutorial]):
        def _push(pk: int):
            # The project and tutorial must be marked as pending before push
            assert model.objects.get(pk=pk).firebase_push_status == FirebasePushStatusEnum.PENDING
            model.objects.filter(pk=pk).update(firebase_push_status=FirebasePushStatusEnum.SUCCESS)
            return True

        return mock.Mock(side_effect=_push)

    def test_dry_run(self):
        with (
            mock.patch(
                "apps.project.management.commands.push_media_urls_to_firebase.push_project_to_firebase",
            ) as push_project_mock,
            mock.patch(
                "apps.project.management.commands.push_media_urls_to_firebase.push_tutorial_to_firebase",
            ) as push_tutorial_mock,
        ):
            output = self.call_command("--dry-run")

        push_project_mock.assert_not_called()
        push_tutorial_mock.assert_not_called()
        for project in [self.published_project, self.paused_project]:
            assert f"Would push Project(id: {project.pk}," in output
            assert f"Would push Tutorial(id: {project.tutorial_id}," in output
        for project in [self.finished_project, self.not_pushed_project]:
            assert f"Project(id: {project.pk}," not in output
            assert f"Tutorial(id: {project.tutorial_id}," not in output
        assert "Dry run: tutorials=2 projects=2 skipped=0 failed=0" in output

    def test_push(self):
        push_project_mock = self.mock_push(Project)
        push_tutorial_mock = self.mock_push(Tutorial)
        with (
            mock.patch(
                "apps.project.management.commands.push_media_urls_to_firebase.push_project_to_firebase",
                push_project_mock,
            ),
            mock.patch(
                "apps.project.management.commands.push_media_urls_to_firebase.push_tutorial_to_firebase",
                push_tutorial_mock,
            ),
        ):
            output = self.call_command("--project-ids", str(self.paused_project.pk), str(self.finished_project.pk))

        push_project_mock.assert_called_once_with(self.paused_project.pk)
        push_tutorial_mock.assert_called_once_with(self.paused_project.tutorial_id)
        assert "tutorials=1 projects=1 skipped=0 failed=0" in output

    def test_push_skipped_when_locked(self):
        project = self.paused_project
        with (
            mock.patch(
                "apps.project.management.commands.push_media_urls_to_firebase.push_tutorial_to_firebase",
                self.mock_push(Tutorial),
            ),
            CeleryLock.redis_lock(CeleryLock.Key.PUSH_PROJECT_TO_FIREBASE.format(project.pk)) as acquired,
        ):
            assert acquired
            output = self.call_command("--project-ids", str(project.pk))

        assert "tutorials=1 projects=1 skipped=1 failed=0" in output
        project.refresh_from_db()
        # Not left in PENDING
        assert project.firebase_push_status == FirebasePushStatusEnum.SUCCESS

import importlib
import typing

from django.apps import apps
from django.db.models import F
from django.test import override_settings
from django.utils import timezone
from ulid import ULID

from apps.common.models import AssetTypeEnum
from apps.project.factories import OrganizationFactory, ProjectAssetFactory, ProjectFactory
from apps.project.models import Project, ProjectAsset, ProjectAssetExportTypeEnum, ProjectStatusEnum
from apps.user.factories import UserFactory
from main.tests import TestCase

migration_module = importlib.import_module(
    "apps.project.migrations.0018_move_active_project_exports_to_short_term_file",
)
move_exports_to_short_term_file = migration_module.move_exports_to_short_term_file
move_exports_to_file = migration_module.move_exports_to_file


class TestShortTermStorageMigrations(TestCase):
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

    def create_project(self, status: ProjectStatusEnum) -> Project:
        return ProjectFactory.create(
            **self.user_resource_kwargs,
            requesting_organization=self.organization,
            status=status,
        )

    def create_asset(self, project: Project, asset_type: AssetTypeEnum, file_name: str) -> ProjectAsset:
        return ProjectAssetFactory.create(
            **self.user_resource_kwargs,
            project=project,
            client_id=str(ULID()),
            type=asset_type,
            export_type=ProjectAssetExportTypeEnum.RESULTS if asset_type == AssetTypeEnum.EXPORT else None,
            file=file_name,
            file_size=10,
        )

    def get_file_names(self, assets: dict[str, ProjectAsset]):
        file_names: dict[str, tuple[str | None, str | None]] = {}
        for key, asset in assets.items():
            asset.refresh_from_db()
            file_names[key] = (asset.file.name or None, asset.short_term_file.name or None)
        return file_names

    def create_assets(self):
        return {
            f"{status.name}-{asset_type.name}": self.create_asset(
                self.create_project(status),
                asset_type,
                f"project/{status.name}/asset/{asset_type.name}/file.csv",
            )
            for status in [
                ProjectStatusEnum.DRAFT,
                ProjectStatusEnum.PUBLISHED,
                ProjectStatusEnum.PAUSED,
                ProjectStatusEnum.FINISHED,
                ProjectStatusEnum.WITHDRAWN,
            ]
            for asset_type in [AssetTypeEnum.EXPORT, AssetTypeEnum.INPUT]
        }

    @override_settings(SHORT_TERM_STORAGE_ENABLED=False)
    def test_disabled(self):
        assets = self.create_assets()
        file_names = self.get_file_names(assets)

        move_exports_to_short_term_file(apps, None)

        assert self.get_file_names(assets) == file_names

    @override_settings(SHORT_TERM_STORAGE_ENABLED=True)
    def test_enabled(self):
        assets = self.create_assets()
        ProjectAsset.objects.filter(pk=assets["PUBLISHED-EXPORT"].pk).update(promoted_at=timezone.now())
        # Exports of an ended project which are not promoted yet
        finished_short_term_asset = self.create_asset(
            self.create_project(ProjectStatusEnum.FINISHED),
            AssetTypeEnum.EXPORT,
            "project/FINISHED-SHORT-TERM/asset/EXPORT/file.csv",
        )
        ProjectAsset.objects.filter(pk=finished_short_term_asset.pk).update(file=None, short_term_file=F("file"))
        assets["FINISHED-SHORT-TERM-EXPORT"] = finished_short_term_asset
        initial_file_names = self.get_file_names(assets)
        assert initial_file_names["FINISHED-SHORT-TERM-EXPORT"] == (
            None,
            "project/FINISHED-SHORT-TERM/asset/EXPORT/file.csv",
        )

        move_exports_to_short_term_file(apps, None)

        assert self.get_file_names(assets) == {
            **initial_file_names,
            "PUBLISHED-EXPORT": (None, "project/PUBLISHED/asset/EXPORT/file.csv"),
            "PAUSED-EXPORT": (None, "project/PAUSED/asset/EXPORT/file.csv"),
        }
        assert assets["PUBLISHED-EXPORT"].promoted_at is None

        # Reverse
        move_exports_to_file(apps, None)
        assert self.get_file_names(assets) == initial_file_names

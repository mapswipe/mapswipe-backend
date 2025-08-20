import typing

from asgiref.sync import sync_to_async
from django.utils.functional import cached_property
from strawberry.dataloader import DataLoader

from apps.common.models import AssetTypeEnum
from apps.project.models import ProjectAsset
from apps.project.models import ProjectAssetExportTypeEnum as AssetStatsEnum

if typing.TYPE_CHECKING:
    from .types.types import ProjectAssetType


def load_export_assets(export_type: AssetStatsEnum):
    def load_export_assets_(keys: list[int]) -> list["ProjectAssetType | None"]:
        qs = ProjectAsset.objects.filter(
            project__in=keys,
            type=AssetTypeEnum.EXPORT,
            export_type=export_type,
        )

        map_ = {asset.project_id: asset for asset in qs.all()}

        return [map_.get(key) for key in keys]  # type: ignore[ProjectAssetType]

    return load_export_assets_


class ProjectExportDataLoader:
    @cached_property
    def aggregated_results(self):
        return DataLoader(load_fn=sync_to_async(load_export_assets(AssetStatsEnum.AGGREGATED_RESULTS)))

    @cached_property
    def aggregated_results_with_geometry(self):
        return DataLoader(load_fn=sync_to_async(load_export_assets(AssetStatsEnum.AGGREGATED_RESULTS_WITH_GEOMETRY)))

    @cached_property
    def groups(self):
        return DataLoader(load_fn=sync_to_async(load_export_assets(AssetStatsEnum.GROUPS)))

    @cached_property
    def history(self):
        return DataLoader(load_fn=sync_to_async(load_export_assets(AssetStatsEnum.HISTORY)))

    @cached_property
    def results(self):
        return DataLoader(load_fn=sync_to_async(load_export_assets(AssetStatsEnum.RESULTS)))

    @cached_property
    def tasks(self):
        return DataLoader(load_fn=sync_to_async(load_export_assets(AssetStatsEnum.TASKS)))

    @cached_property
    def users(self):
        return DataLoader(load_fn=sync_to_async(load_export_assets(AssetStatsEnum.USERS)))

    @cached_property
    def area_of_interest(self):
        return DataLoader(load_fn=sync_to_async(load_export_assets(AssetStatsEnum.AREA_OF_INTEREST)))

    @cached_property
    def hot_tasking_manager_geometries(self):
        return DataLoader(load_fn=sync_to_async(load_export_assets(AssetStatsEnum.HOT_TASKING_MANAGER_GEOMETRIES)))

    @cached_property
    def moderate_to_high_agreement_yes_maybe_geometries(self):
        return DataLoader(
            load_fn=sync_to_async(load_export_assets(AssetStatsEnum.MODERATE_TO_HIGH_AGREEMENT_YES_MAYBE_GEOMETRIES)),
        )


class ProjectDataLoader:
    @cached_property
    def export(self):
        return ProjectExportDataLoader()

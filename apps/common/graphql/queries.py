import typing

import strawberry
import strawberry_django

from apps.common.graphql.types import GlobalExportAssetType
from apps.common.models import GlobalExportAsset, GlobalExportAssetTypeEnum


@strawberry.type
class Query:
    global_export_assets: list[GlobalExportAssetType] = strawberry_django.field()

    @strawberry_django.field
    def global_export_asset(self, asset_type: GlobalExportAssetTypeEnum) -> GlobalExportAssetType:
        return typing.cast(
            "GlobalExportAssetType",
            GlobalExportAsset.objects.get(type=asset_type),
        )

import strawberry
import strawberry_django
from strawberry_django.pagination import OffsetPaginated
from strawberry_django.permissions import IsAuthenticated

from utils.geo.raster_tile_server.config import RasterConfig, RasterTileServerNameEnum, RasterTileServerNameEnumWithoutCustom
from utils.geo.vector_tile_server.config import VectorConfig, VectorTileServerNameEnum, VectorTileServerNameEnumWithoutCustom

from .filters import OrganizationFilter, ProjectAssetFilter, ProjectFilter
from .orders import OrganizationOrder, ProjectAssetOrder, ProjectOrder
from .types.project_types.base import RasterTileServersType, RasterTileServerType, VectorTileServerType
from .types.types import (
    OrganizationType,
    ProjectAssetType,
    ProjectType,
)


def get_tile_servers() -> RasterTileServersType:
    def _get_raster_tile_server_type(enum: RasterTileServerNameEnumWithoutCustom):
        config = RasterConfig.get_config(enum)
        return RasterTileServerType(
            type=enum,
            label=str(enum.label),
            url=config["url"],
            credits=config["credits"],
        )

    def _get_vector_tile_server_type(enum: VectorTileServerNameEnumWithoutCustom):
        return VectorTileServerType(
            type=enum,
            label=str(enum.label),
            **VectorConfig.get_config(enum),
        )

    return RasterTileServersType(
        vector=[
            _get_vector_tile_server_type(VectorTileServerNameEnum.OPEN_STREET_MAP),
            _get_vector_tile_server_type(VectorTileServerNameEnum.VERSATILES),
            _get_vector_tile_server_type(VectorTileServerNameEnum.OPEN_FREE_MAP),
        ],
        raster=[
            _get_raster_tile_server_type(RasterTileServerNameEnum.BING),
            _get_raster_tile_server_type(RasterTileServerNameEnum.MAPBOX),
            _get_raster_tile_server_type(RasterTileServerNameEnum.MAXAR_STANDARD),
            _get_raster_tile_server_type(RasterTileServerNameEnum.MAXAR_PREMIUM),
            _get_raster_tile_server_type(RasterTileServerNameEnum.ESRI),
            _get_raster_tile_server_type(RasterTileServerNameEnum.ESRI_BETA),
        ],
    )


@strawberry.type
class Query:
    tile_servers: RasterTileServersType = strawberry.field(resolver=get_tile_servers, extensions=[IsAuthenticated()])

    # Private --------------------
    project: ProjectType = strawberry_django.field(extensions=[IsAuthenticated()])

    # --- Paginated
    projects: OffsetPaginated[ProjectType] = strawberry_django.offset_paginated(
        order=ProjectOrder,
        filters=ProjectFilter,
        extensions=[IsAuthenticated()],
    )

    project_asset: ProjectAssetType = strawberry_django.field(extensions=[IsAuthenticated()])

    # --- Paginated
    project_assets: OffsetPaginated[ProjectAssetType] = strawberry_django.offset_paginated(
        order=ProjectAssetOrder,
        filters=ProjectAssetFilter,
        extensions=[IsAuthenticated()],
    )

    organization: OrganizationType = strawberry_django.field(extensions=[IsAuthenticated()])

    # --- Paginated
    organizations: OffsetPaginated[OrganizationType] = strawberry_django.offset_paginated(
        order=OrganizationOrder,
        filters=OrganizationFilter,
        extensions=[IsAuthenticated()],
    )

import strawberry
import strawberry_django
from strawberry_django.pagination import OffsetPaginated
from strawberry_django.permissions import IsAuthenticated

from utils.geo.raster_tile_server.config import RasterConfig, RasterTileServerNameEnum
from utils.geo.vector_tile_server.config import VectorConfig, VectorTileServerNameEnum

from .filters import OrganizationFilter, ProjectAssetFilter, ProjectFilter
from .orders import OrganizationOrder, ProjectAssetOrder, ProjectOrder
from .types.project_types.base import RasterTileServersType, RasterTileServerType, VectorTileServerType
from .types.types import (
    OrganizationType,
    ProjectAssetType,
    ProjectType,
)


def get_tile_servers() -> RasterTileServersType:
    vector_tiles = [
        VectorTileServerType(
            type=VectorTileServerNameEnum.OPEN_STREET_MAP,
            label=VectorTileServerNameEnum.OPEN_STREET_MAP.label,
            **VectorConfig.get_config(VectorTileServerNameEnum.OPEN_STREET_MAP),
        ),
        VectorTileServerType(
            type=VectorTileServerNameEnum.VERSATILES,
            label=VectorTileServerNameEnum.VERSATILES.label,
            **VectorConfig.get_config(VectorTileServerNameEnum.VERSATILES),
        ),
        VectorTileServerType(
            type=VectorTileServerNameEnum.OPEN_FREE_MAP,
            label=VectorTileServerNameEnum.OPEN_FREE_MAP.label,
            **VectorConfig.get_config(VectorTileServerNameEnum.OPEN_FREE_MAP),
        ),
    ]
    raster_tiles = [
        RasterTileServerType(
            type=RasterTileServerNameEnum.BING,
            label=RasterTileServerNameEnum.BING.label,
            **RasterConfig.get_config(RasterTileServerNameEnum.BING),
        ),
        RasterTileServerType(
            type=RasterTileServerNameEnum.MAPBOX,
            label=RasterTileServerNameEnum.MAPBOX.label,
            **RasterConfig.get_config(RasterTileServerNameEnum.MAPBOX),
        ),
        RasterTileServerType(
            type=RasterTileServerNameEnum.MAXAR_STANDARD,
            label=RasterTileServerNameEnum.MAXAR_STANDARD.label,
            **RasterConfig.get_config(RasterTileServerNameEnum.MAXAR_STANDARD),
        ),
        RasterTileServerType(
            type=RasterTileServerNameEnum.MAXAR_PREMIUM,
            label=RasterTileServerNameEnum.MAXAR_PREMIUM.label,
            **RasterConfig.get_config(RasterTileServerNameEnum.MAXAR_PREMIUM),
        ),
        RasterTileServerType(
            type=RasterTileServerNameEnum.ESRI,
            label=RasterTileServerNameEnum.ESRI.label,
            **RasterConfig.get_config(RasterTileServerNameEnum.ESRI),
        ),
        RasterTileServerType(
            type=RasterTileServerNameEnum.ESRI_BETA,
            label=RasterTileServerNameEnum.ESRI_BETA.label,
            **RasterConfig.get_config(RasterTileServerNameEnum.ESRI_BETA),
        ),
    ]
    return RasterTileServersType(
        vector=vector_tiles,
        raster=raster_tiles,
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

import strawberry
import strawberry_django
from django.db.models import QuerySet
from strawberry_django.pagination import OffsetPaginated
from strawberry_django.permissions import IsAuthenticated

from apps.project.models import Organization, Project
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

    project_asset: ProjectAssetType = strawberry_django.field(extensions=[IsAuthenticated()])

    # --- Paginated
    project_assets: OffsetPaginated[ProjectAssetType] = strawberry_django.offset_paginated(
        order=ProjectAssetOrder,
        filters=ProjectAssetFilter,
        extensions=[IsAuthenticated()],
    )

    organization: OrganizationType = strawberry_django.field(extensions=[IsAuthenticated()])

    # --- Paginated
    @strawberry_django.offset_paginated(
        OffsetPaginated[OrganizationType],
        order=OrganizationOrder,
        filters=OrganizationFilter,
        extensions=[IsAuthenticated()],
    )
    def organizations(
        self,
        include_all: bool = False,
    ) -> QuerySet[Organization]:
        if include_all:
            return Organization.objects.all()
        return Organization.objects.exclude(is_archived=True).all()

    # --- Paginated
    @strawberry_django.offset_paginated(
        OffsetPaginated[ProjectType],
        order=ProjectOrder,
        filters=ProjectFilter,
        extensions=[IsAuthenticated()],
    )
    def projects(
        self,
        include_all: bool = False,
    ) -> QuerySet[Project]:
        if include_all:
            return Project.objects.all()
        return Project.objects.exclude(status__in=[Project.Status.ARCHIVED, Project.Status.DISCARDED]).all()

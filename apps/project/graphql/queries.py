import strawberry
import strawberry_django
from strawberry_django.pagination import OffsetPaginated
from strawberry_django.permissions import IsAuthenticated

from utils.geo.tile_server.config import Config, TileServerNameEnum
from utils.geo.vector_tile_server.config import VectorConfig, VectorTileServerNameEnum

from .filters import OrganizationFilter, ProjectAssetFilter, ProjectFilter
from .orders import OrganizationOrder, ProjectAssetOrder, ProjectOrder
from .types import (
    OrganizationType,
    ProjectAssetType,
    ProjectType,
    RasterTileServerType,
    TileServersType,
    VectorTileServerType,
)


def get_tile_servers() -> TileServersType:
    vector_tiles = [
        VectorTileServerType(
            type=VectorTileServerNameEnum.OPEN_STREET_MAP,
            label=VectorTileServerNameEnum.OPEN_STREET_MAP.label,
            url=VectorConfig.VECTOR_IMAGE_URLS[VectorTileServerNameEnum.OPEN_STREET_MAP],
            # FIXME(tnagorra): Need to check what layers we want
            # FIXME(tnagorra): Should we also include the source: versatiles-shortbread
            min_zoom=0,
            max_zoom=14,
            layers=[
                "buildings",
                "boundaries",
                "bridges",
                "dam_lines",
                "dam_polygons",
                "ferries",
                "land",
                "ocean",
                "pier_lines",
                "pier_polygons",
                "sites",
                "street_polygons",
                "streets",
                "water_lines",
                "water_polygons",
            ],
            credits="Map data from OpenStreetMap",
        ),
        VectorTileServerType(
            type=VectorTileServerNameEnum.VERSATILES,
            label=VectorTileServerNameEnum.VERSATILES.label,
            url=VectorConfig.VECTOR_IMAGE_URLS[VectorTileServerNameEnum.VERSATILES],
            # FIXME(tnagorra): Need to check what layers we want
            # FIXME(tnagorra): Should we also include the source: versatiles-shortbread
            min_zoom=0,
            max_zoom=14,
            layers=[
                "buildings",
                "boundaries",
                "bridges",
                "dam_lines",
                "dam_polygons",
                "ferries",
                "land",
                "ocean",
                "pier_lines",
                "pier_polygons",
                "sites",
                "street_polygons",
                "streets",
                "water_lines",
                "water_polygons",
            ],
            credits="Map data from OpenStreetMap",
        ),
        VectorTileServerType(
            type=VectorTileServerNameEnum.OPEN_FREE_MAP,
            label=VectorTileServerNameEnum.OPEN_FREE_MAP.label,
            url=VectorConfig.VECTOR_IMAGE_URLS[VectorTileServerNameEnum.OPEN_FREE_MAP],
            # FIXME(tnagorra): Need to check what layers we want
            # FIXME(tnagorra): Should we also include the source: openmaptiles
            min_zoom=0,
            max_zoom=14,
            layers=[
                "building",
                "aeroway",
                "boundary",
                "landcover",
                "landuse",
                "park",
                "transportation",
                "water",
                "waterway",
            ],
            credits="OpenFreeMap © OpenMapTiles Data from OpenStreetMap",
        ),
    ]
    raster_tiles = [
        RasterTileServerType(
            type=TileServerNameEnum.BING,
            label=TileServerNameEnum.BING.label,
            url=Config.IMAGE_URLS_WITH_KEY[TileServerNameEnum.BING],
            credits="© 2019 Microsoft Corporation, Earthstar Geographics SIO",
        ),
        RasterTileServerType(
            type=TileServerNameEnum.MAPBOX,
            label=TileServerNameEnum.MAPBOX.label,
            url=Config.IMAGE_URLS_WITH_KEY[TileServerNameEnum.MAPBOX],
            credits="© 2019 MapBox",
        ),
        RasterTileServerType(
            type=TileServerNameEnum.MAXAR_STANDARD,
            label=TileServerNameEnum.MAXAR_STANDARD.label,
            url=Config.IMAGE_URLS_WITH_KEY[TileServerNameEnum.MAXAR_STANDARD],
            credits="© 2019 Maxar",
        ),
        RasterTileServerType(
            type=TileServerNameEnum.MAXAR_PREMIUM,
            label=TileServerNameEnum.MAXAR_PREMIUM.label,
            url=Config.IMAGE_URLS_WITH_KEY[TileServerNameEnum.MAXAR_PREMIUM],
            credits="© 2019 Maxar",
        ),
        RasterTileServerType(
            type=TileServerNameEnum.ESRI,
            label=TileServerNameEnum.ESRI.label,
            url=Config.IMAGE_URLS_WITH_KEY[TileServerNameEnum.ESRI],
            credits="© 2019 ESRI",
        ),
        RasterTileServerType(
            type=TileServerNameEnum.ESRI_BETA,
            label=TileServerNameEnum.ESRI_BETA.label,
            url=Config.IMAGE_URLS_WITH_KEY[TileServerNameEnum.ESRI_BETA],
            credits="© 2019 ESRI",
        ),
    ]
    return TileServersType(
        vector=vector_tiles,
        raster=raster_tiles,
    )


@strawberry.type
class Query:
    tile_servers: TileServersType = strawberry.field(resolver=get_tile_servers, extensions=[IsAuthenticated()])

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

import strawberry
import strawberry_django
from strawberry_django.pagination import OffsetPaginated
from strawberry_django.permissions import IsAuthenticated

from utils.geo.raster_tile_server.config import Config, RasterTileServerNameEnum
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
            type=RasterTileServerNameEnum.BING,
            label=RasterTileServerNameEnum.BING.label,
            url=Config.IMAGE_URLS_WITH_KEY[RasterTileServerNameEnum.BING],
            credits="© 2019 Microsoft Corporation, Earthstar Geographics SIO",
        ),
        RasterTileServerType(
            type=RasterTileServerNameEnum.MAPBOX,
            label=RasterTileServerNameEnum.MAPBOX.label,
            url=Config.IMAGE_URLS_WITH_KEY[RasterTileServerNameEnum.MAPBOX],
            credits="© 2019 MapBox",
        ),
        RasterTileServerType(
            type=RasterTileServerNameEnum.MAXAR_STANDARD,
            label=RasterTileServerNameEnum.MAXAR_STANDARD.label,
            url=Config.IMAGE_URLS_WITH_KEY[RasterTileServerNameEnum.MAXAR_STANDARD],
            credits="© 2019 Maxar",
        ),
        RasterTileServerType(
            type=RasterTileServerNameEnum.MAXAR_PREMIUM,
            label=RasterTileServerNameEnum.MAXAR_PREMIUM.label,
            url=Config.IMAGE_URLS_WITH_KEY[RasterTileServerNameEnum.MAXAR_PREMIUM],
            credits="© 2019 Maxar",
        ),
        RasterTileServerType(
            type=RasterTileServerNameEnum.ESRI,
            label=RasterTileServerNameEnum.ESRI.label,
            url=Config.IMAGE_URLS_WITH_KEY[RasterTileServerNameEnum.ESRI],
            credits="© 2019 ESRI",
        ),
        RasterTileServerType(
            type=RasterTileServerNameEnum.ESRI_BETA,
            label=RasterTileServerNameEnum.ESRI_BETA.label,
            url=Config.IMAGE_URLS_WITH_KEY[RasterTileServerNameEnum.ESRI_BETA],
            credits="© 2019 ESRI",
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

import strawberry
import strawberry_django
from strawberry_django.pagination import OffsetPaginated
from strawberry_django.permissions import IsAuthenticated

from .filters import ProjectAssetFilter, ProjectFilter
from .orders import ProjectAssetOrder, ProjectOrder
from .types import ProjectAssetType, ProjectType


@strawberry.type
class Query:
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

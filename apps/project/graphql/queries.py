import strawberry
import strawberry_django
from strawberry_django.pagination import OffsetPaginated
from strawberry_django.permissions import IsAuthenticated

from .filters import ProjectFilter
from .orders import ProjectOrder
from .types import ProjectType


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

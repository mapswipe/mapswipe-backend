import strawberry
import strawberry_django
from strawberry_django.pagination import OffsetPaginated
from strawberry_django.permissions import IsAuthenticated

from .filters import TutorialFilter
from .orders import TutorialOrder
from .types.types import TutorialType


@strawberry.type
class Query:
    # Private --------------------
    tutorial: TutorialType = strawberry_django.field(extensions=[IsAuthenticated()])

    # --- Paginated
    tutorials: OffsetPaginated[TutorialType] = strawberry_django.offset_paginated(
        order=TutorialOrder,
        filters=TutorialFilter,
        extensions=[IsAuthenticated()],
    )

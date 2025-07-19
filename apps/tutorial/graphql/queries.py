import strawberry
import strawberry_django
from django.db.models import QuerySet
from strawberry_django.pagination import OffsetPaginated
from strawberry_django.permissions import IsAuthenticated

from apps.tutorial.models import Tutorial

from .filters import TutorialFilter
from .orders import TutorialOrder
from .types.types import TutorialType


@strawberry.type
class Query:
    # Private --------------------
    tutorial: TutorialType = strawberry_django.field(extensions=[IsAuthenticated()])

    # --- Paginated
    @strawberry_django.offset_paginated(
        OffsetPaginated[TutorialType],
        order=TutorialOrder,
        filters=TutorialFilter,
        extensions=[IsAuthenticated()],
    )
    def tutorials(
        self,
        include_all: bool = False,
    ) -> QuerySet[Tutorial]:
        if include_all:
            return Tutorial.objects.all()
        return Tutorial.objects.exclude(status__in=[Tutorial.Status.ARCHIVED, Tutorial.Status.DISCARDED]).all()

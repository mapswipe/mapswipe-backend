import strawberry
import strawberry_django
from django.db.models import QuerySet
from strawberry_django.pagination import OffsetPaginated
from strawberry_django.permissions import IsAuthenticated

from apps.tutorial.models import Tutorial, TutorialAsset

from .filters import TutorialAssetFilter, TutorialFilter
from .orders import TutorialAssetOrder, TutorialOrder
from .types.types import TutorialAssetType, TutorialType


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
    # TODO: We need attribute description `include_all` visible in graphiql
    def tutorials(
        self,
        include_all: bool = False,
    ) -> QuerySet[Tutorial]:
        if include_all:
            return Tutorial.objects.all()
        return Tutorial.objects.filter(status=Tutorial.Status.PUBLISHED).all()

    tutorial_asset: TutorialAssetType = strawberry_django.field(extensions=[IsAuthenticated()])

    # --- Paginated
    @strawberry_django.offset_paginated(
        OffsetPaginated[TutorialAssetType],
        order=TutorialAssetOrder,
        filters=TutorialAssetFilter,
        extensions=[IsAuthenticated()],
    )
    def tutorial_assets(
        self,
        include_all: bool = False,
    ) -> QuerySet[TutorialAsset]:
        if include_all:
            return TutorialAsset.objects.all()
        return TutorialAsset.usable_objects()

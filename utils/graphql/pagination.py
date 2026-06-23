import typing
from typing import Any, Self

import strawberry
from django.conf import settings
from django.db.models import QuerySet
from strawberry.types import Info
from strawberry.types.unset import UNSET
from strawberry_django.pagination import NodeType, OffsetPaginated, OffsetPaginationInput


@strawberry.type
class PublicOffsetPaginated(OffsetPaginated[NodeType]):
    """OffsetPaginated subclass that enforces PUBLIC_PAGINATION_MAX_LIMIT."""

    @typing.override
    @classmethod
    def resolve_paginated(
        cls,
        queryset: QuerySet,
        *,
        info: Info,
        pagination: OffsetPaginationInput | None = None,
        **kwargs: Any,
    ) -> Self:
        max_limit: int | None = getattr(settings, "STRAWBERRY_DJANGO", {}).get("PUBLIC_PAGINATION_MAX_LIMIT")
        assert max_limit is not None, "STRAWBERRY_DJANGO.PUBLIC_PAGINATION_MAX_LIMIT must be set in settings"

        if pagination is None:
            pagination = OffsetPaginationInput(offset=0, limit=max_limit)
        else:
            limit = pagination.limit
            if limit is UNSET or limit is None or limit < 0 or limit > max_limit:
                pagination = OffsetPaginationInput(offset=pagination.offset, limit=max_limit)
        return super().resolve_paginated(queryset, info=info, pagination=pagination, **kwargs)

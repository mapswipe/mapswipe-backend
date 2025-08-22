import typing

import strawberry_django
from django.db import models
from django.db.models.base import Model


def unaccented_filter[T: Model](
    field_name: str,
    qs_alias: typing.Callable[[models.QuerySet[T], str], models.QuerySet[T]] | None = None,
):
    @strawberry_django.filter_field
    @staticmethod
    def wrapper(
        queryset: models.QuerySet[T],
        value: str,
        prefix: str,
    ) -> tuple[models.QuerySet[T], models.Q]:
        if qs_alias:
            queryset = qs_alias(queryset, prefix)
        lookup = f"{field_name}__unaccent__icontains"
        return queryset, models.Q(**{lookup: value})

    return wrapper

import strawberry_django
from django.db import models


def unaccented_filter(field_name: str):
    """Decorator to create unaccented string filters"""

    def decorator(func):
        @strawberry_django.filter_field
        def wrapper(
            self,
            queryset: models.QuerySet,
            value: str,
            prefix: str,
        ) -> tuple[models.QuerySet, models.Q]:
            lookup = f"{field_name}__unaccent__icontains"
            return queryset, models.Q(**{lookup: value})

        return wrapper

    return decorator

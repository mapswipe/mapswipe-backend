import strawberry
import strawberry_django
from django.db import models

from apps.user.models import User


@strawberry_django.filters.filter(User, lookups=True)
class UserFilter:
    id: strawberry.auto

    @strawberry_django.filter_field
    def display_name(
        self,
        queryset: models.QuerySet[User],
        value: str,
        prefix: str,
    ) -> tuple[models.QuerySet[User], models.Q]:
        return queryset, models.Q(display_name__unaccent__icontains=value)

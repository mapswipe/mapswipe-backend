import strawberry
import strawberry_django
from django.db import models

from apps.common.filters import unaccented_filter
from apps.contributor.graphql.filters import ContributorUserFilter
from apps.user.models import User


@strawberry_django.filters.filter(User, lookups=True)
class UserFilter:
    id: strawberry.auto
    contributor_user: ContributorUserFilter | None = strawberry.UNSET
    display_name = unaccented_filter("display_name")

    @strawberry_django.filter_field
    def search(
        self,
        queryset: models.QuerySet[User],
        value: str,
        prefix: str,
    ) -> tuple[models.QuerySet[User], models.Q]:
        return queryset, models.Q(
            **{
                f"{prefix}display_name__icontains": value,
            },
        ) | models.Q(
            **{
                f"{prefix}contributor_user__username__icontains": value,
            },
        )

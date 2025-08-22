import strawberry
import strawberry_django

from apps.common.filters import unaccented_filter
from apps.user.models import User


@strawberry_django.filters.filter(User, lookups=True)
class UserFilter:
    id: strawberry.auto

    display_name = unaccented_filter("display_name")

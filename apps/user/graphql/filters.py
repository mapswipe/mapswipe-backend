import strawberry
import strawberry_django

from apps.common.filters import unaccented_filter
from apps.user.models import User


@strawberry_django.filters.filter(User, lookups=True)
class UserFilter:
    id: strawberry.auto

    @unaccented_filter("display_name")
    def display_name(self):
        pass

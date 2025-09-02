import typing

import strawberry
import strawberry_django

from apps.user.models import User

if typing.TYPE_CHECKING:
    from apps.contributor.graphql.types import ContributorUserType


@strawberry_django.type(User)
class UserType:
    id: strawberry.ID
    first_name: strawberry.auto
    last_name: strawberry.auto
    display_name: strawberry.auto
    anonymized_email: str

    contributor_user: typing.Annotated["ContributorUserType", strawberry.lazy("apps.contributor.graphql.types")] | None


@strawberry_django.type(User)
class UserMeType(UserType):
    email: strawberry.auto

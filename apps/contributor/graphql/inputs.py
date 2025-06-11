import strawberry
import strawberry_django

from apps.common.graphql.inputs import (
    UserResourceCreateInputMixin,
    UserResourceTopLevelUpdateInputMixin,
)
from apps.contributor.models import ContributorUserGroup


@strawberry_django.input(ContributorUserGroup)
class ContributorUserGroupCreateInput(UserResourceCreateInputMixin):
    name: strawberry.auto
    description: strawberry.auto


@strawberry_django.partial(ContributorUserGroup)
class ContributorUserGroupUpdateInput(UserResourceTopLevelUpdateInputMixin):
    name: strawberry.auto
    description: strawberry.auto
    is_archived: strawberry.auto

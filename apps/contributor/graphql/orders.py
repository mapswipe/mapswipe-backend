import strawberry
import strawberry_django

from apps.contributor.models import ContributorUser, ContributorUserGroup, ContributorUserGroupMembership


@strawberry_django.ordering.order(ContributorUser)
class ContributorUserOrder:
    id: strawberry.auto
    username: strawberry.auto


@strawberry_django.ordering.order(ContributorUserGroup)
class ContributorUserGroupOrder:
    id: strawberry.auto
    name: strawberry.auto


@strawberry_django.ordering.order(ContributorUserGroupMembership)
class ContributorUserGroupMembershipOrder:
    id: strawberry.auto

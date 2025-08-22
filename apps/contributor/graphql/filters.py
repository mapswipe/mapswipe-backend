import strawberry
import strawberry_django
from django.db import models

from apps.common.filters import unaccented_filter
from apps.contributor.models import ContributorTeam, ContributorUser, ContributorUserGroup, ContributorUserGroupMembership


@strawberry_django.filters.filter(ContributorUser, lookups=True)
class ContributorUserFilter:
    id: strawberry.auto
    firebase_id: strawberry.auto
    username: strawberry.auto
    team_id: strawberry.auto


@strawberry_django.filters.filter(ContributorUserGroup, lookups=True)
class ContributorUserGroupFilter:
    id: strawberry.auto
    is_archived: strawberry.auto

    name = unaccented_filter("name")

    @staticmethod
    def _filter_by_user(
        user_field: str,
        queryset: models.QuerySet[ContributorUserGroup],
        value: str,
    ) -> tuple[models.QuerySet[ContributorUserGroup], models.Q]:
        membership_qs = ContributorUserGroupMembership.objects.filter(
            is_active=True,
            **{
                user_field: value,
            },
        )

        return queryset, models.Q(
            id__in=membership_qs.values("user_group_id"),
        )

    @strawberry_django.filter_field
    def user_firebase_id(
        self,
        queryset: models.QuerySet[ContributorUserGroup],
        value: strawberry.ID,
        prefix: str,
    ) -> tuple[models.QuerySet[ContributorUserGroup], models.Q]:
        return self._filter_by_user("user__firebase_id", queryset, value)


@strawberry_django.filters.filter(ContributorUserGroupMembership, lookups=True)
class ContributorUserGroupMembershipFilter:
    id: strawberry.auto
    user_group_id: strawberry.auto


@strawberry_django.filters.filter(ContributorTeam, lookups=True)
class ContributorTeamFilter:
    id: strawberry.auto
    is_archived: strawberry.auto

    name = unaccented_filter("name")

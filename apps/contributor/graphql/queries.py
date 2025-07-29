import typing

import strawberry
import strawberry_django
from django.db.models import QuerySet
from django.shortcuts import aget_object_or_404
from strawberry_django.pagination import OffsetPaginated
from strawberry_django.permissions import IsAuthenticated

from apps.contributor.models import ContributorTeam, ContributorUser, ContributorUserGroup, ContributorUserGroupMembership

from .filters import (
    ContributorTeamFilter,
    ContributorUserFilter,
    ContributorUserGroupFilter,
    ContributorUserGroupMembershipFilter,
)
from .orders import (
    ContributorTeamOrder,
    ContributorUserGroupMembershipOrder,
    ContributorUserGroupOrder,
    ContributorUserOrder,
)
from .types import ContributorTeamType, ContributorUserGroupMembershipType, ContributorUserGroupType, ContributorUserType


@strawberry.type
class Query:
    contributor_users: OffsetPaginated[ContributorUserType] = strawberry_django.offset_paginated(
        order=ContributorUserOrder,
        filters=ContributorUserFilter,
    )

    contributor_user: ContributorUserType = strawberry_django.field()

    contributor_user_group: ContributorUserGroupType = strawberry_django.field()

    # Team
    contributor_team: ContributorTeamType = strawberry_django.field()

    @strawberry.field
    async def contributor_user_by_user_id(self, user_id: strawberry.ID) -> ContributorUserType:
        obj = await aget_object_or_404(ContributorUser, user_id=user_id)
        return typing.cast("ContributorUserType", obj)

    # --- Paginated
    # --- ContributorUserGroup
    @strawberry_django.offset_paginated(
        OffsetPaginated[ContributorUserGroupType],
        order=ContributorUserGroupOrder,
        filters=ContributorUserGroupFilter,
    )
    # TODO: We need attribute description `include_all` visible in graphiql
    def contributor_user_groups(
        self,
        include_all: bool = False,
    ) -> QuerySet[ContributorUserGroup]:
        # XXX: Filter out user group without name. They aren't sync yet.
        # TODO: This is from old system, make sure name aren't empty and remove this filter
        queryset = ContributorUserGroup.objects.exclude(name="").all()
        if include_all:
            return queryset
        return queryset.exclude(is_archived=True).all()

    # --- Paginated
    # --- ContributorUserGroupMembership
    @strawberry_django.offset_paginated(
        OffsetPaginated[ContributorUserGroupMembershipType],
        order=ContributorUserGroupMembershipOrder,
        filters=ContributorUserGroupMembershipFilter,
    )
    # TODO: We need attribute description `include_all` visible in graphiql
    def contributor_user_group_members(
        self,
        include_all: bool = False,
    ) -> QuerySet[ContributorUserGroupMembership]:
        queryset = ContributorUserGroupMembership.objects.all()
        if include_all:
            return queryset
        return queryset.exclude(is_active=False).all()

    # --- Paginated
    # --- Team
    @strawberry_django.offset_paginated(
        OffsetPaginated[ContributorTeamType],
        order=ContributorTeamOrder,
        filters=ContributorTeamFilter,
        extensions=[IsAuthenticated()],
    )
    # TODO: We need attribute description `include_all` visible in graphiql
    def contributor_teams(
        self,
        include_all: bool = False,
    ) -> QuerySet[ContributorTeam]:
        if include_all:
            return ContributorTeam.objects.all()
        return ContributorTeam.objects.exclude(is_archived=True).all()

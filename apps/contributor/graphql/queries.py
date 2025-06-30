import typing

import strawberry
import strawberry_django
from django.shortcuts import aget_object_or_404
from strawberry_django.pagination import OffsetPaginated

from apps.contributor.models import ContributorUser

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

    contributor_user_groups: OffsetPaginated[ContributorUserGroupType] = strawberry_django.offset_paginated(
        order=ContributorUserGroupOrder,
        filters=ContributorUserGroupFilter,
    )

    contributor_user_group: ContributorUserGroupType = strawberry_django.field()

    contributor_user_group_members: OffsetPaginated[ContributorUserGroupMembershipType] = strawberry_django.offset_paginated(
        order=ContributorUserGroupMembershipOrder,
        filters=ContributorUserGroupMembershipFilter,
    )

    # Team
    contributor_team: ContributorTeamType = strawberry_django.field()
    contributor_teams: OffsetPaginated[ContributorTeamType] = strawberry_django.offset_paginated(
        order=ContributorTeamOrder,
        filters=ContributorTeamFilter,
    )

    @strawberry.field
    async def contributor_user_by_user_id(self, user_id: strawberry.ID) -> ContributorUserType:
        obj = await aget_object_or_404(ContributorUser, user_id=user_id)
        return typing.cast("ContributorUserType", obj)

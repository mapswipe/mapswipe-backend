import datetime
from dataclasses import InitVar
from dataclasses import field as dataclass_field

import strawberry
from asgiref.sync import sync_to_async
from django.db import models
from django.utils import timezone

from apps.community_dashboard.models import AggregatedUserGroupStatData, AggregatedUserStatData
from apps.contributor.models import ContributorUser, ContributorUserGroup
from utils.graphql.inputs import FirebaseOrInternalIdInputType

from .types import (
    AggregateHelper,
    CommunityStatsType,
    ContributorTimeStatType,
    ContributorUserGroupStats,
    ContributorUserStats,
    DateRangeInput,
    MapContributionStatsType,
    OrganizationSwipeStatsType,
    ProjectTypeAreaStatsType,
    ProjectTypeSwipeStatsType,
)


# TODO: Cache this
@sync_to_async
def get_community_stats() -> CommunityStatsType:
    user_agg_data = AggregatedUserStatData.objects.aggregate(
        swipes_sum=models.Sum("swipes"),
        total_users=models.Count("user", distinct=True),
    )
    user_group_agg_data = AggregatedUserGroupStatData.objects.aggregate(
        total_user_groups=models.Count("user_group", distinct=True),
    )
    return CommunityStatsType(
        id=strawberry.ID("all"),
        total_contributors=user_agg_data["total_users"] or 0,
        total_user_groups=user_group_agg_data["total_user_groups"] or 0,
        total_swipes=user_agg_data["swipes_sum"] or 0,
    )


# TODO: Cache this
@sync_to_async
def get_community_stats_latest() -> CommunityStatsType:
    """Stats from last 30 days."""
    date_threshold = timezone.now() - datetime.timedelta(days=30)
    user_agg_data = AggregatedUserStatData.objects.filter(timestamp_date__gte=date_threshold).aggregate(
        swipes_sum=models.Sum("swipes"),
        total_users=models.Count("user", distinct=True),
    )
    user_group_agg_data = AggregatedUserGroupStatData.objects.filter(timestamp_date__gte=date_threshold).aggregate(
        total_user_groups=models.Count("user_group", distinct=True),
    )
    return CommunityStatsType(
        id=strawberry.ID("last-30-days"),
        total_contributors=user_agg_data["total_users"] or 0,
        total_user_groups=user_group_agg_data["total_user_groups"] or 0,
        total_swipes=user_agg_data["swipes_sum"] or 0,
    )


@strawberry.type
class CommunityFilteredStats:
    date_range: InitVar[DateRangeInput | None]

    _qs: strawberry.Private[models.QuerySet[AggregatedUserStatData]] = dataclass_field(init=False)
    _qs_cte: strawberry.Private[models.QuerySet[AggregatedUserStatData]] = dataclass_field(init=False)

    def __post_init__(self, date_range: DateRangeInput | None):
        filters = {}
        if date_range:
            filters.update(
                timestamp_date__gte=date_range.from_date,
                timestamp_date__lte=date_range.to_date,
            )
        self._qs = AggregatedUserStatData.objects.filter(**filters)
        self._qs_cte = AggregatedUserStatData.cte_objects.filter(**filters)

    @strawberry.field
    async def swipe_time_by_date(self) -> list[ContributorTimeStatType]:
        return await AggregateHelper.get_swipe_time_by_date(self._qs)

    @strawberry.field
    async def area_swiped_by_project_type(self) -> list[ProjectTypeAreaStatsType]:
        return await AggregateHelper.get_area_swiped_by_project_type(self._qs)

    @strawberry.field
    async def swipe_by_project_type(self) -> list[ProjectTypeSwipeStatsType]:
        return await AggregateHelper.get_swipe_by_project_type(self._qs)

    @strawberry.field
    async def swipe_by_organization_name(self) -> list[OrganizationSwipeStatsType]:
        return await AggregateHelper.get_swipe_by_organization_name(self._qs)

    @strawberry.field
    async def swipe_by_project_geo(self) -> list[MapContributionStatsType]:
        return await AggregateHelper.get_swipe_by_project_geo(self._qs_cte)


@strawberry.type
class Query:
    community_stats: CommunityStatsType = strawberry.field(resolver=get_community_stats)
    community_stats_latest: CommunityStatsType = strawberry.field(
        resolver=get_community_stats_latest,
        description=get_community_stats_latest.__doc__,
    )

    @strawberry.field
    async def community_filtered_stats(
        self,
        # FIXME(thenav56): Remove the None?
        date_range: DateRangeInput | None = None,
    ) -> CommunityFilteredStats:
        return CommunityFilteredStats(date_range=date_range)

    # By Internal ID
    @strawberry.field
    async def community_user_stats(
        self,
        user_id: FirebaseOrInternalIdInputType,
    ) -> ContributorUserStats:
        user = await FirebaseOrInternalIdInputType.aget_object_or_404(ContributorUser, object_id=user_id)
        return ContributorUserStats(user=user)

    @strawberry.field
    async def community_user_group_stats(
        self,
        user_group_id: FirebaseOrInternalIdInputType,
    ) -> ContributorUserGroupStats:
        user_group = await FirebaseOrInternalIdInputType.aget_object_or_404(ContributorUserGroup, object_id=user_group_id)
        return ContributorUserGroupStats(user_group=user_group)

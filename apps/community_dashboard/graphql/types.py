import datetime
import json
import typing
from dataclasses import InitVar
from dataclasses import field as dataclass_field

import strawberry
import strawberry_django
from django.db import models
from django.utils import timezone
from django_cte import With  # type: ignore[reportMissingTypeStubs]

from apps.community_dashboard.models import AggregatedUserGroupStatData, AggregatedUserStatData
from apps.contributor.models import ContributorUser, ContributorUserGroup
from apps.project.models import Project, ProjectTypeEnum
from utils.graphql.inputs import DateRangeInput
from utils.graphql.types import AreaSqKm, GenericJSON

# TODO(thenav56): Add cache for heavy operations


class AggregateHelper:
    type QuerySet = models.QuerySet[AggregatedUserGroupStatData | AggregatedUserStatData]

    @staticmethod
    async def get_swipe_by_project_type(qs: QuerySet) -> list["ProjectTypeSwipeStatsType"]:
        qs_ = (
            qs.order_by()
            .values("project__project_type")
            .annotate(swipes_sum=models.Sum("swipes"))
            .values_list(
                "project__project_type",
                "swipes_sum",
            )
        )
        return [
            ProjectTypeSwipeStatsType(
                project_type=project_type,
                total_swipes=swipes_sum or 0,
            )
            async for project_type, swipes_sum in qs_
        ]

    @staticmethod
    async def get_swipe_by_organization_name(qs: QuerySet) -> list["OrganizationSwipeStatsType"]:
        qs_ = (
            qs.order_by()
            .values("project__requesting_organization__name")
            .annotate(
                total_swipes=models.Sum("swipes"),
            )
            .values_list(
                "project__requesting_organization__name",
                "total_swipes",
            )
        )
        return [
            OrganizationSwipeStatsType(
                organization_name=organization_name or "MapSwipe",
                total_swipes=total_swipes,
            )
            async for organization_name, total_swipes in qs_
        ]

    @staticmethod
    async def get_area_swiped_by_project_type(qs: QuerySet) -> list["ProjectTypeAreaStatsType"]:
        qs_ = (
            qs.filter(area_swiped__isnull=False)
            .order_by()
            .values("project__project_type")
            .annotate(
                total_area_swiped=models.Sum("area_swiped"),
            )
            .values_list(
                "project__project_type",
                "total_area_swiped",
            )
        )
        return [
            ProjectTypeAreaStatsType(
                project_type=project_type,
                total_area=AreaSqKm(area_sum),
            )
            async for project_type, area_sum in qs_
        ]

    @staticmethod
    async def get_swipe_time_by_date(qs: QuerySet) -> list["ContributorTimeStatType"]:
        qs_ = (
            qs.filter(total_time__isnull=False)
            .order_by("timestamp_date")
            .values("timestamp_date")
            .annotate(
                total_time_sum=models.Sum("total_time"),
            )
            .values_list(
                "timestamp_date",
                "total_time_sum",
            )
        )
        return [
            ContributorTimeStatType(
                date=date,
                total_swipe_time=total_time_sum,
            )
            async for date, total_time_sum in qs_
        ]

    @staticmethod
    async def get_swipe_by_date(qs: QuerySet) -> list["ContributorSwipeStatType"]:
        qs_ = (
            qs.filter(task_count__isnull=False)
            .order_by("timestamp_date")
            .values("timestamp_date")
            .annotate(total_swipes=models.Sum("swipes"))
            .values_list(
                "timestamp_date",
                "total_swipes",
            )
        )
        return [
            ContributorSwipeStatType(
                task_date=task_date,
                total_swipes=swipe_count,
            )
            async for task_date, swipe_count in qs_
        ]

    # XXX: qs_cte type is wrong
    @staticmethod
    async def get_swipe_by_project_geo(qs_cte: QuerySet) -> list["MapContributionStatsType"]:
        project_qs = Project.cte_objects.filter(centroid__isnull=False).values("id", "centroid")
        agg_data_qs = (
            qs_cte.order_by()
            .values("project")
            .annotate(swipes_sum=models.Sum("swipes"))
            .values_list(
                "project_id",
                "swipes_sum",
            )
        )
        project_qs_with = With(project_qs, name="project_data")
        agg_data_qs_with = With(agg_data_qs, name="aggregated_data")
        qs = (
            project_qs_with.join(
                agg_data_qs_with.queryset(),
                project_id=project_qs_with.col.id,
            )
            .with_cte(project_qs_with)  # type: ignore[reportAttributeAccessIssue]
            .with_cte(agg_data_qs_with)
            .values_list(
                project_qs_with.col.centroid,
                "swipes_sum",
            )
        )
        return [
            MapContributionStatsType(
                geojson=json.loads(geojson.json),
                total_contribution=total_contribution,
            )
            async for geojson, total_contribution in qs
        ]


@strawberry.type
class CommunityStatsType:
    id: strawberry.ID
    total_swipes: int
    total_contributors: int
    total_user_groups: int


@strawberry.type
class ProjectTypeAreaStatsType:
    project_type: ProjectTypeEnum
    total_area: AreaSqKm

    @strawberry.field
    def project_type_display(self) -> str:
        return str(ProjectTypeEnum(self.project_type).label)


@strawberry.type
class ProjectTypeSwipeStatsType:
    project_type: ProjectTypeEnum
    total_swipes: int

    @strawberry.field
    def project_type_display(self) -> str:
        return ProjectTypeEnum.get_display(self.project_type)


@strawberry.type
class ContributorUserGroupStatsType:
    total_swipes: int
    total_swipe_time: int = strawberry.field(description="total swipe time (seconds)")
    total_mapping_projects: int
    total_contributors: int
    total_area_swiped: AreaSqKm
    total_organization: int


@strawberry.type
class ContributorUserGroupLatestStatsType:
    total_swipes: int
    total_swipe_time: int = strawberry.field(description="total swipe time (seconds)")
    total_mapping_projects: int
    total_contributors: int


@strawberry.type
class ContributorUserGroupUserStatsType:
    user_id: str
    username: str | None
    total_mapping_projects: int
    total_swipes: int
    total_swipe_time: int = strawberry.field(description="total swipe time (seconds)")


@strawberry.type
class ContributorUserStatType:
    total_swipes: int
    total_swipe_time: int = strawberry.field(description="total swipe time (seconds)")
    total_mapping_projects: int
    total_area_swiped: AreaSqKm
    total_organization: int


@strawberry.type
class ContributorSwipeStatType:
    task_date: datetime.date
    total_swipes: int


@strawberry.type
class ContributorTimeStatType:
    date: datetime.date
    total_swipe_time: int = strawberry.field(description="total swipe time (seconds)")


@strawberry.type
class OrganizationSwipeStatsType:
    organization_name: str
    total_swipes: int


@strawberry.type
class MapContributionStatsType:
    geojson: GenericJSON
    total_contribution: int


@strawberry.type
class ContributorUserLatestStatsType:
    total_swipes: int
    total_swipe_time: int = strawberry.field(description="total swipe time (seconds)")
    total_user_groups: int


@strawberry.interface
class ContributorUserUserGroupBaseFilterStatsQuery:
    date_range: InitVar[DateRangeInput | None]

    qs_: strawberry.Private[models.QuerySet[AggregatedUserStatData | AggregatedUserGroupStatData] | None] = dataclass_field(
        init=False,
    )
    qs_cte_: strawberry.Private[models.QuerySet[AggregatedUserStatData | AggregatedUserGroupStatData] | None] = (
        dataclass_field(init=False)
    )

    @property
    def qs(self):
        if self.qs_ is None:
            raise Exception("qs should be defined")
        return self.qs_

    @property
    def qs_cte(self):
        if self.qs_cte_ is None:
            raise Exception("qs should be defined")
        return self.qs_cte_

    @strawberry.field
    async def swipe_by_date(self) -> list[ContributorSwipeStatType]:
        return await AggregateHelper.get_swipe_by_date(self.qs)

    @strawberry.field
    async def swipe_time_by_date(self) -> list[ContributorTimeStatType]:
        return await AggregateHelper.get_swipe_time_by_date(self.qs)

    @strawberry.field
    async def area_swiped_by_project_type(self) -> list[ProjectTypeAreaStatsType]:
        return await AggregateHelper.get_area_swiped_by_project_type(self.qs)

    @strawberry.field
    async def swipe_by_project_type(self) -> list[ProjectTypeSwipeStatsType]:
        return await AggregateHelper.get_swipe_by_project_type(self.qs)

    @strawberry_django.field
    async def swipe_by_organization_name(self) -> list[OrganizationSwipeStatsType]:
        return await AggregateHelper.get_swipe_by_organization_name(self.qs)

    @strawberry.field
    async def swipe_by_project_geo(self) -> list[MapContributionStatsType]:
        return await AggregateHelper.get_swipe_by_project_geo(self.qs_cte)


@strawberry.type
class ContributorUserFilteredStats(ContributorUserUserGroupBaseFilterStatsQuery):
    date_range: InitVar[DateRangeInput | None]
    user: InitVar[ContributorUser]

    # Internal
    _user: strawberry.Private[ContributorUser] = dataclass_field(init=False)

    def __post_init__(self, date_range: DateRangeInput | None, user: ContributorUser):
        filters: dict[str, typing.Any] = {
            "user": user,
        }
        self._user = user
        if date_range is not None:
            filters.update(
                timestamp_date__gte=date_range.from_date,
                timestamp_date__lte=date_range.to_date,
            )
        self.qs_ = AggregatedUserStatData.objects.filter(**filters)
        self.qs_cte_ = AggregatedUserStatData.cte_objects.filter(**filters)

    @strawberry.field
    async def id(self) -> strawberry.ID:
        return typing.cast("strawberry.ID", self._user.pk)


@strawberry.type
class ContributorUserStats:
    user: InitVar[ContributorUser]

    # Internal
    _user: strawberry.Private[ContributorUser] = dataclass_field(init=False)
    u_qs: strawberry.Private[models.QuerySet[AggregatedUserStatData]] = dataclass_field(init=False)
    ug_qs: strawberry.Private[models.QuerySet[AggregatedUserGroupStatData]] = dataclass_field(init=False)

    def __post_init__(self, user: ContributorUser):
        self._user = user
        self.u_qs = AggregatedUserStatData.objects.filter(user=user)
        self.ug_qs = AggregatedUserGroupStatData.objects.filter(user=user)

    @strawberry.field
    async def id(self) -> strawberry.ID:
        return typing.cast("strawberry.ID", self._user.pk)

    @strawberry.field
    async def firebase_id(self) -> strawberry.ID:
        return typing.cast("strawberry.ID", self._user.firebase_id)

    @strawberry.field
    async def stats(self) -> ContributorUserStatType:
        # TODO: Cache this
        agg_data = await self.u_qs.aaggregate(
            total_swipes=models.Sum("swipes"),
            total_time_sum=models.Sum("total_time"),
            total_project=models.Count("project_id"),
            total_area_swiped=models.Sum("area_swiped"),
            total_organization=models.Count(
                "project__requesting_organization__name",
                distinct=True,
            ),
        )
        return ContributorUserStatType(
            total_swipes=agg_data["total_swipes"] or 0,
            total_swipe_time=int(agg_data["total_time_sum"] or 0),
            total_mapping_projects=agg_data["total_project"] or 0,
            total_area_swiped=AreaSqKm(agg_data["total_area_swiped"] or 0),
            total_organization=agg_data["total_organization"] or 0,
        )

    @strawberry.field(description="Stats from last 30 days")
    async def stats_latest(self) -> ContributorUserLatestStatsType:
        date_threshold = timezone.now() - datetime.timedelta(days=30)
        agg_data = await self.u_qs.filter(timestamp_date__gte=date_threshold).aaggregate(
            total_swipes=models.Sum("swipes"),
            total_time_sum=models.Sum("total_time"),
        )
        total_group_count = (
            await self.ug_qs.aaggregate(
                count=models.Count(
                    "user_group_id",
                    distinct=True,
                    filter=models.Q(user_group_id__isnull=False),
                ),
            )
        )["count"]
        return ContributorUserLatestStatsType(
            total_swipes=agg_data["total_swipes"] or 0,
            total_swipe_time=int(agg_data["total_time_sum"] or 0),
            total_user_groups=total_group_count or 0,
        )

    @strawberry.field
    async def filtered_stats(
        self,
        date_range: DateRangeInput | None = None,
    ) -> ContributorUserFilteredStats:
        return ContributorUserFilteredStats(
            user=self._user,
            date_range=date_range,
        )


@strawberry.type
class ContributorUserGroupFilteredStats(ContributorUserUserGroupBaseFilterStatsQuery):
    date_range: InitVar[DateRangeInput | None]
    user_group_id: InitVar[int]

    def __post_init__(self, date_range: DateRangeInput | None, user_group_id: int):
        filters: dict[str, typing.Any] = {
            "user_group_id": user_group_id,
        }
        if date_range:
            filters.update(
                timestamp_date__gte=date_range.from_date,
                timestamp_date__lte=date_range.to_date,
            )
        self.qs_ = AggregatedUserGroupStatData.objects.filter(**filters)
        self.qs_cte_ = AggregatedUserGroupStatData.cte_objects.filter(**filters)


@strawberry.type
class ContributorUserGroupStats:
    user_group: InitVar[ContributorUserGroup]

    _user_group_id: strawberry.Private[int] = dataclass_field(init=False)
    _ug_qs: strawberry.Private[models.QuerySet[AggregatedUserGroupStatData]] = dataclass_field(init=False)

    def __post_init__(self, user_group: ContributorUserGroup):
        self._user_group_id = user_group.pk
        self._ug_qs = AggregatedUserGroupStatData.objects.filter(
            user_group_id=user_group.pk,
        )

    @strawberry.field
    async def id(self) -> strawberry.ID:
        return typing.cast("strawberry.ID", self._user_group_id)

    @strawberry.field
    async def stats(self) -> ContributorUserGroupStatsType:
        agg_data = await self._ug_qs.aaggregate(
            total_swipes=models.Sum("swipes"),
            total_time_sum=models.Sum("total_time"),
            total_contributors=models.Count("user_id", distinct=True),
            total_project=models.Count("project_id", distinct=True),
            total_area_swiped=models.Sum("area_swiped"),
            total_organization=models.Count(
                "project__requesting_organization__name",
                distinct=True,
            ),
        )
        return ContributorUserGroupStatsType(
            total_swipes=agg_data["total_swipes"] or 0,
            total_swipe_time=int(agg_data["total_time_sum"] or 0),
            total_contributors=agg_data["total_contributors"] or 0,
            total_mapping_projects=agg_data["total_project"] or 0,
            total_area_swiped=AreaSqKm(agg_data["total_area_swiped"] or 0),
            total_organization=agg_data["total_organization"] or 0,
        )

    @strawberry.field(description="Stats from last 30 days")
    async def stats_latest(self) -> ContributorUserGroupLatestStatsType:
        date_threshold = timezone.now() - datetime.timedelta(days=30)
        agg_data = await self._ug_qs.filter(timestamp_date__gte=date_threshold).aaggregate(
            total_swipes=models.Sum("swipes"),
            total_time_sum=models.Sum("total_time"),
            total_contributors=models.Count("user_id", distinct=True),
            total_project=models.Count("project_id", distinct=True),
        )
        return ContributorUserGroupLatestStatsType(
            total_swipes=agg_data["total_swipes"] or 0,
            total_swipe_time=int(agg_data["total_time_sum"] or 0),
            total_contributors=agg_data["total_contributors"] or 0,
            total_mapping_projects=agg_data["total_project"] or 0,
        )

    @strawberry.field
    async def filtered_stats(
        self,
        date_range: DateRangeInput | None = None,
    ) -> ContributorUserGroupFilteredStats:
        return ContributorUserGroupFilteredStats(
            user_group_id=self._user_group_id,
            date_range=date_range,
        )

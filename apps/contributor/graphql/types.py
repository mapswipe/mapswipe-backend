import strawberry
import strawberry_django
from django.db import models
from django.db.models.functions import Coalesce
from strawberry_django.pagination import OffsetPaginated

from apps.common.graphql.types import ArchivableResourceTypeMixin, UserResourceTypeMixin
from apps.community_dashboard.models import AggregatedUserGroupStatData, AggregatedUserStatData
from apps.contributor.models import ContributorTeam, ContributorUser, ContributorUserGroup, ContributorUserGroupMembership


# TODO(thenav56): Test N+1
def generate_aggregated_user_stat_data_annotate(agg: models.Count | models.Sum):
    return Coalesce(
        models.Subquery(
            AggregatedUserStatData.objects.filter(
                user_id=models.OuterRef("user_id"),
            )
            .order_by()
            .values("user_id")
            .annotate(c=agg)
            .values("c")[:1],
            output_field=models.IntegerField(),
        ),
        0,
    )


def generate_aggregated_user_group_stat_data_annotate(agg: models.Count | models.Sum):
    return Coalesce(
        models.Subquery(
            AggregatedUserGroupStatData.objects.filter(
                user_id=models.OuterRef("user_id"),
                user_group_id=models.OuterRef("user_group_id"),
            )
            .order_by()
            .values("user_id")
            .annotate(c=agg)
            .values("c")[:1],
            output_field=models.IntegerField(),
        ),
        0,
    )


@strawberry_django.type(ContributorUser)
class ContributorUserType:
    id: strawberry.ID
    user_id: strawberry.ID
    username: strawberry.auto
    created_at: strawberry.auto

    # Stats
    total_mapping_projects: int = strawberry_django.field(
        annotate=generate_aggregated_user_stat_data_annotate(models.Count("project", distinct=True)),
    )

    total_swipes: int = strawberry_django.field(
        annotate=generate_aggregated_user_stat_data_annotate(models.Sum("swipes")),
    )

    total_swipe_time: int = strawberry_django.field(
        annotate=generate_aggregated_user_stat_data_annotate(models.Sum("total_time")),
    )


@strawberry_django.type(ContributorUserGroup)
class ContributorUserGroupType(UserResourceTypeMixin, ArchivableResourceTypeMixin):
    id: strawberry.ID
    name: strawberry.auto
    description: strawberry.auto

    members_count: int = strawberry_django.field(
        annotate=Coalesce(
            models.Subquery(
                ContributorUserGroupMembership.objects.filter(
                    user_group_id=models.OuterRef("id"),
                )
                .order_by()
                .values("user_group_id")
                .annotate(c=models.Count("user_id"))
                .values("c")[:1],
                output_field=models.IntegerField(),
            ),
            0,
        ),
    )

    # TODO: Make this a generic module
    # TODO: Add order and filters
    @strawberry_django.offset_paginated(OffsetPaginated["ContributorUserGroupMembershipType"])
    def user_memberships(
        self,
        contributor_user_group: strawberry.Parent[ContributorUserGroup],
    ) -> models.QuerySet[ContributorUserGroupMembership]:
        return ContributorUserGroupMembership.objects.filter(user_group_id=contributor_user_group.pk).order_by("user_id")

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        # XXX: Filter out user group without name. They aren't sync yet.
        # TODO: This is from old system, make sure name aren't empty and remove this filter
        return queryset.exclude(name="")


@strawberry_django.type(ContributorUserGroupMembership)
class ContributorUserGroupMembershipType:
    id: strawberry.ID
    user_id: strawberry.ID
    is_active: strawberry.auto
    user: ContributorUserType

    # Stats
    total_mapping_projects: int = strawberry_django.field(
        annotate=generate_aggregated_user_group_stat_data_annotate(models.Count("project", distinct=True)),
    )

    total_swipes: int = strawberry_django.field(
        annotate=generate_aggregated_user_group_stat_data_annotate(models.Sum("swipes")),
    )

    total_swipe_time: int = strawberry_django.field(
        annotate=generate_aggregated_user_group_stat_data_annotate(models.Sum("total_time")),
    )


@strawberry_django.type(ContributorTeam)
class ContributorTeamType(UserResourceTypeMixin, ArchivableResourceTypeMixin):
    id: strawberry.ID
    name: strawberry.auto

    members_count: int = strawberry_django.field(
        annotate=Coalesce(
            models.Subquery(
                ContributorUser.objects.filter(
                    team_id=models.OuterRef("id"),
                )
                .order_by()
                .values("team_id")
                .annotate(c=models.Count("user_id"))
                .values("c")[:1],
                output_field=models.IntegerField(),
            ),
            0,
        ),
    )

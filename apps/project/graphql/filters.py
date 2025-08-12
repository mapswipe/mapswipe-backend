import strawberry
import strawberry_django
from django.db import models

from apps.project.models import Organization, Project, ProjectAsset


@strawberry_django.filters.filter(Project, lookups=True)
class ProjectFilter:
    id: strawberry.auto
    project_number: strawberry.auto
    project_type: strawberry.auto
    requesting_organization_id: strawberry.auto
    is_featured: strawberry.auto
    status: strawberry.auto
    team: strawberry.auto
    is_private: strawberry.auto

    # NOTE: This might be slow for large datasets, Consider using vector searching in future
    @strawberry_django.filter_field
    def name(
        self,
        queryset: models.QuerySet[Project],
        value: str,
        prefix: str,
    ) -> tuple[models.QuerySet[Project], models.Q]:
        queryset = queryset.alias(
            _name=Project.generate_name_query(prefix),
        )
        return queryset, models.Q(_name__unaccent__icontains=value)

    @strawberry_django.filter_field
    def topic(
        self,
        queryset: models.QuerySet[Project],
        value: str,
        prefix: str,
    ) -> tuple[models.QuerySet[Project], models.Q]:
        return queryset, models.Q(topic__unaccent__icontains=value)

    @strawberry_django.filter_field
    def region(
        self,
        queryset: models.QuerySet[Project],
        value: str,
        prefix: str,
    ) -> tuple[models.QuerySet[Project], models.Q]:
        return queryset, models.Q(region__unaccent__icontains=value)


@strawberry_django.filters.filter(ProjectAsset, lookups=True)
class ProjectAssetFilter:
    id: strawberry.auto
    type: strawberry.auto
    input_type: strawberry.auto
    export_type: strawberry.auto
    mimetype: strawberry.auto
    project_id: strawberry.auto


@strawberry_django.filters.filter(Organization, lookups=True)
class OrganizationFilter:
    id: strawberry.auto
    is_archived: strawberry.auto

    @strawberry_django.filter_field
    def name(
        self,
        queryset: models.QuerySet[Organization],
        value: str,
        prefix: str,
    ) -> tuple[models.QuerySet[Organization], models.Q]:
        return queryset, models.Q(name__unaccent__icontains=value)

import strawberry
import strawberry_django
from django.db import models

from apps.project.models import Organization, Project, ProjectAsset


@strawberry_django.filters.filter(Project, lookups=True)
class ProjectFilter:
    id: strawberry.auto
    topic: strawberry.auto
    project_number: strawberry.auto
    region: strawberry.auto
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
        return queryset, models.Q(_name__icontains=value)


@strawberry_django.filters.filter(ProjectAsset, lookups=True)
class ProjectAssetFilter:
    id: strawberry.auto
    type: strawberry.auto
    mimetype: strawberry.auto
    project_id: strawberry.auto


@strawberry_django.filters.filter(Organization, lookups=True)
class OrganizationFilter:
    id: strawberry.auto
    name: strawberry.auto
    is_archived: strawberry.auto

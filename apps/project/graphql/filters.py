import strawberry
import strawberry_django

from apps.project.models import Organization, Project, ProjectAsset


@strawberry_django.filters.filter(Project, lookups=True)
class ProjectFilter:
    id: strawberry.auto
    name: strawberry.auto
    project_type: strawberry.auto
    requesting_organization_id: strawberry.auto
    is_featured: strawberry.auto
    status: strawberry.auto


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

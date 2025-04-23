import strawberry
import strawberry_django

from apps.project.models import Project


@strawberry_django.filters.filter(Project, lookups=True)
class ProjectFilter:
    id: strawberry.auto
    name: strawberry.auto
    project_type: strawberry.auto
    requesting_organization: strawberry.auto
    is_featured: strawberry.auto
    status: strawberry.auto

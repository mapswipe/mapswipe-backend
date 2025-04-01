import strawberry
import strawberry_django

from ..models import Project


@strawberry_django.filters.filter(Project, lookups=True)
class ProjectFilter:
    id: strawberry.auto
    name: strawberry.auto

import strawberry
import strawberry_django

from apps.project.models import Project


@strawberry_django.ordering.order(Project)
class ProjectOrder:
    id: strawberry.auto
    name: strawberry.auto

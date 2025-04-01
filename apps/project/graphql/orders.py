import strawberry
import strawberry_django

from ..models import Project


@strawberry_django.ordering.order(Project)
class ProjectOrder:
    id: strawberry.auto
    name: strawberry.auto

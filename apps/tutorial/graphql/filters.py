import strawberry
import strawberry_django

from apps.project.graphql.filters import ProjectFilter
from apps.tutorial.models import Tutorial


@strawberry_django.filters.filter(Tutorial, lookups=True)
class TutorialFilter:
    id: strawberry.auto
    name: strawberry.auto
    status: strawberry.auto
    project: ProjectFilter | None

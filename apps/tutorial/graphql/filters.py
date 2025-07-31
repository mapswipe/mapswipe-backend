import strawberry
import strawberry_django

from apps.project.graphql.filters import ProjectFilter
from apps.tutorial.models import Tutorial, TutorialAsset


@strawberry_django.filters.filter(Tutorial, lookups=True)
class TutorialFilter:
    id: strawberry.auto
    name: strawberry.auto
    status: strawberry.auto
    project: ProjectFilter | None


@strawberry_django.filters.filter(TutorialAsset, lookups=True)
class TutorialAssetFilter:
    id: strawberry.auto
    type: strawberry.auto
    mimetype: strawberry.auto
    tutorial_id: strawberry.auto

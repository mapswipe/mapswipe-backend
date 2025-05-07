import strawberry
import strawberry_django

from apps.tutorial.models import Tutorial


@strawberry_django.filters.filter(Tutorial, lookups=True)
class TutorialFilter:
    id: strawberry.auto
    is_draft: strawberry.auto

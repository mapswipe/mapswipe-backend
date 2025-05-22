import strawberry
import strawberry_django

from apps.tutorial.models import Tutorial


@strawberry_django.ordering.order(Tutorial)
class TutorialOrder:
    id: strawberry.auto
    name: strawberry.auto

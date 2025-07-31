import strawberry
import strawberry_django

from apps.tutorial.models import Tutorial, TutorialAsset


@strawberry_django.ordering.order(Tutorial)
class TutorialOrder:
    id: strawberry.auto
    name: strawberry.auto


@strawberry_django.ordering.order(TutorialAsset)
class TutorialAssetOrder:
    id: strawberry.auto

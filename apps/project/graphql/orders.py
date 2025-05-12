import strawberry
import strawberry_django

from apps.project.models import Organization, Project, ProjectAsset


@strawberry_django.ordering.order(Project)
class ProjectOrder:
    id: strawberry.auto
    name: strawberry.auto


@strawberry_django.ordering.order(ProjectAsset)
class ProjectAssetOrder:
    id: strawberry.auto


@strawberry_django.ordering.order(Organization)
class OrganizationOrder:
    id: strawberry.auto
    name: strawberry.auto

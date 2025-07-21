import strawberry
import strawberry_django
from django.db import models
from django.db.models.expressions import OrderBy

from apps.project.models import Organization, Project, ProjectAsset


@strawberry_django.ordering.order(Project)
class ProjectOrder:
    id: strawberry.auto
    topic: strawberry.auto

    @strawberry_django.order_field
    def name(
        self,
        queryset: models.QuerySet[Project],
        value: strawberry_django.Ordering,
        prefix: str,
    ) -> tuple[models.QuerySet[Project], list[OrderBy]]:
        queryset = queryset.alias(
            _name=Project.generate_name_query(prefix),
        )
        ordering = value.resolve(f"{prefix}_name")
        return queryset, [ordering]


@strawberry_django.ordering.order(ProjectAsset)
class ProjectAssetOrder:
    id: strawberry.auto


@strawberry_django.ordering.order(Organization)
class OrganizationOrder:
    id: strawberry.auto
    name: strawberry.auto

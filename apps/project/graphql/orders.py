import strawberry
import strawberry_django
from django.db import models
from django.db.models.expressions import OrderBy, Value
from django.db.models.functions import Concat

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
            _name=Concat(
                models.F(f"{prefix}topic"),
                Value(" "),
                models.F(f"{prefix}region"),
                Value(" "),
                models.F(f"{prefix}project_number"),
                Value(" "),
                models.F(f"{prefix}requesting_organization__name"),
                output_field=models.CharField(),
            ),
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

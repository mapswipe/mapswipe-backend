import strawberry
import strawberry_django

from apps.common.filters import unaccented_filter
from apps.project.models import Organization, Project, ProjectAsset


@strawberry_django.filters.filter(Project, lookups=True)
class ProjectFilter:
    id: strawberry.auto
    project_number: strawberry.auto
    project_type: strawberry.auto
    requesting_organization_id: strawberry.auto
    is_featured: strawberry.auto
    status: strawberry.auto
    team: strawberry.auto
    is_private: strawberry.auto

    topic = unaccented_filter("topic")
    region = unaccented_filter("region")
    name = unaccented_filter(
        "_name",
        qs_alias=lambda queryset, prefix: queryset.alias(
            _name=Project.generate_name_query(prefix),
        ),
    )


@strawberry_django.filters.filter(ProjectAsset, lookups=True)
class ProjectAssetFilter:
    id: strawberry.auto
    type: strawberry.auto
    input_type: strawberry.auto
    export_type: strawberry.auto
    mimetype: strawberry.auto
    project_id: strawberry.auto


@strawberry_django.filters.filter(Organization, lookups=True)
class OrganizationFilter:
    id: strawberry.auto
    is_archived: strawberry.auto

    name = unaccented_filter("name")

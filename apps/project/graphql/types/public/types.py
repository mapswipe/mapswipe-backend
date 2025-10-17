import datetime

import strawberry
import strawberry_django

from apps.project.graphql.types.types import GeometryType, OrganizationType, ProjectAssetType, ProjectExportAssetTypeMixin
from apps.project.models import Project


# Project
@strawberry_django.type(Project)
class PublicProjectType(ProjectExportAssetTypeMixin):
    id: strawberry.ID
    firebase_id: str
    project_type: strawberry.auto
    requesting_organization_id: strawberry.ID
    requesting_organization: OrganizationType
    region: strawberry.auto
    description: strawberry.auto
    image: ProjectAssetType | None
    status: strawberry.auto
    created_at: datetime.datetime
    modified_at: datetime.datetime

    total_area: strawberry.auto
    aoi_geometry: GeometryType | None

    number_of_contributor_users: strawberry.auto

    @strawberry_django.field(
        description=str(Project._meta.get_field("progress").help_text),  # type: ignore[reportAttributeAccessIssue]
    )
    def progress(self, project: strawberry.Parent[Project]) -> float:
        return project.progress / 100

    @strawberry_django.field(
        only=["topic", "region", "project_number", "requesting_organization__name", "project_type"],
        annotate={"generated_name": Project.generate_name_query()},
        description="Project name generated from topic, region, project number, and requesting organization name.",
    )
    def name(self, project: strawberry.Parent[Project]) -> str:
        return project.generated_name  # type: ignore[reportAttributeAccessIssue]

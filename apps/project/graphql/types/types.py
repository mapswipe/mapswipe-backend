import typing

import strawberry
import strawberry_django

from apps.common.graphql.types import UserResourceTypeMixin
from apps.contributor.graphql.types import ContributorTeamType
from apps.project.models import Organization, Project, ProjectAsset
from apps.tutorial.graphql.types.types import TutorialType
from project_types.tile_map_service.compare import project as compare_project
from project_types.tile_map_service.completeness import project as completeness_project
from project_types.tile_map_service.find import project as find_project
from project_types.validate import project as validate_project
from project_types.validate_image import project as validate_image_project

# NOTE: We are importing base for side-effect
# The tile server types are required by the following imports
from .project_types import base  # noqa: F401  # isort: skip # type: ignore[reportUnusedImport]

from .project_types.compare import CompareProjectPropertyType
from .project_types.completeness import CompletenessProjectPropertyType
from .project_types.find import FindProjectPropertyType
from .project_types.validate import ValidateProjectPropertyType
from .project_types.validate_image import ValidateImageProjectPropertyType


# Organization
@strawberry_django.type(Organization)
class OrganizationType(UserResourceTypeMixin):
    id: strawberry.ID
    name: strawberry.auto


# Project
@strawberry_django.type(ProjectAsset)
class ProjectAssetType(UserResourceTypeMixin):
    id: strawberry.ID
    type: strawberry.auto
    file: strawberry.auto
    mimetype: strawberry.auto
    project_id: strawberry.ID
    marked_as_deleted: strawberry.auto


@strawberry_django.type(Project)
class ProjectType(UserResourceTypeMixin):
    id: strawberry.ID
    project_type: strawberry.auto
    requesting_organization_id: strawberry.ID
    requesting_organization: OrganizationType
    name: strawberry.auto
    look_for: strawberry.auto
    additional_info_url: strawberry.auto
    description: strawberry.auto
    image: ProjectAssetType | None
    tutorial: TutorialType | None
    tutorial_id: strawberry.ID | None
    verification_number: strawberry.auto
    group_size: strawberry.auto
    max_tasks_per_user: strawberry.auto
    is_featured: strawberry.auto
    status: strawberry.auto
    processing_status: strawberry.auto
    progress: strawberry.auto
    team: ContributorTeamType | None
    is_private: strawberry.auto

    @strawberry_django.field(only=["project_type_specifics", "project_type"])
    async def project_type_specifics(
        self,
        project: strawberry.Parent[Project],
    ) -> (
        CompareProjectPropertyType
        | FindProjectPropertyType
        | ValidateProjectPropertyType
        | ValidateImageProjectPropertyType
        | CompletenessProjectPropertyType
        | None
    ):
        data = project.project_type_specifics
        if data is None:
            return None
        if project.project_type_enum == Project.Type.FIND:
            return typing.cast("FindProjectPropertyType", find_project.FindProjectProperty.model_validate(data))
        if project.project_type_enum == Project.Type.COMPARE:
            return typing.cast("CompareProjectPropertyType", compare_project.CompareProjectProperty.model_validate(data))
        if project.project_type_enum == Project.Type.VALIDATE:
            return typing.cast("ValidateProjectPropertyType", validate_project.ValidateProjectProperty.model_validate(data))
        if project.project_type_enum == Project.Type.VALIDATE_IMAGE:
            return typing.cast(
                "ValidateProjectPropertyType",
                validate_image_project.ValidateImageProjectProperty.model_validate(data),
            )
        if project.project_type_enum == Project.Type.COMPLETENESS:
            return typing.cast(
                "CompletenessProjectPropertyType",
                completeness_project.CompletenessProjectProperty.model_validate(data),
            )
        typing.assert_never(project.project_type_enum)

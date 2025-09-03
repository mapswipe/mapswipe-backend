import typing

import strawberry
import strawberry_django

from apps.common.graphql.types import (
    ArchivableResourceTypeMixin,
    CommonAssetTypeMixin,
    FirebasePushResourceTypeMixin,
    UserResourceTypeMixin,
)
from apps.contributor.graphql.types import ContributorTeamType
from apps.project.models import Organization, Project, ProjectAsset, ProjectAssetInputTypeEnum
from apps.tutorial.graphql.types.types import TutorialType
from main.config import Config
from main.graphql.context import Info
from project_types.street import project as street_project
from project_types.tile_map_service.compare import project as compare_project
from project_types.tile_map_service.completeness import project as completeness_project
from project_types.tile_map_service.find import project as find_project
from project_types.validate import project as validate_project
from project_types.validate_image import project as validate_image_project
from utils.asset_types.models import AoiGeometryAssetProperty, ObjectImageAssetProperty

from .asset_types import AoiGeometryAssetPropertyType, ObjectImageAssetPropertyType

# NOTE: We are importing base for side-effect
# The tile server types are required by the following imports
from .project_types import base  # noqa: F401  # isort: skip # type: ignore[reportUnusedImport]


from .project_types.compare import CompareProjectPropertyType
from .project_types.completeness import CompletenessProjectPropertyType
from .project_types.find import FindProjectPropertyType
from .project_types.street import StreetProjectPropertyType
from .project_types.validate import ValidateProjectPropertyType
from .project_types.validate_image import ValidateImageProjectPropertyType


# Organization
@strawberry_django.type(Organization)
class OrganizationType(UserResourceTypeMixin, ArchivableResourceTypeMixin, FirebasePushResourceTypeMixin):
    id: strawberry.ID
    name: strawberry.auto
    description: strawberry.auto
    abbreviation: strawberry.auto


# Project
@strawberry_django.type(ProjectAsset)
class ProjectAssetType(UserResourceTypeMixin, CommonAssetTypeMixin):
    id: strawberry.ID
    file: strawberry.auto
    export_type: strawberry.auto
    input_type: strawberry.auto
    external_url: strawberry.auto
    project_id: strawberry.ID

    @strawberry_django.field(only=["asset_type_specifics", "input_type"])
    async def asset_type_specifics(
        self,
        project_asset: strawberry.Parent[ProjectAsset],
    ) -> AoiGeometryAssetPropertyType | ObjectImageAssetPropertyType | None:
        data = project_asset.asset_type_specifics
        if data is None:
            return None
        if project_asset.input_type_enum == ProjectAssetInputTypeEnum.AOI_GEOMETRY:
            return typing.cast("AoiGeometryAssetPropertyType", AoiGeometryAssetProperty.model_validate(data))
        if project_asset.input_type_enum == ProjectAssetInputTypeEnum.OBJECT_IMAGE:
            return typing.cast("ObjectImageAssetPropertyType", ObjectImageAssetProperty.model_validate(data))
        if project_asset.input_type_enum == ProjectAssetInputTypeEnum.COVER_IMAGE:
            return None
        typing.assert_never(project_asset.input_type_enum)


# Project
@strawberry.interface
class ProjectExportAssetTypeMixin:
    @strawberry.field
    async def export_aggregated_results(self, info: Info, project: strawberry.Parent[Project]) -> ProjectAssetType | None:
        return await info.context.dl.project.export.aggregated_results.load(project.pk)

    @strawberry.field
    async def export_aggregated_results_with_geometry(
        self,
        info: Info,
        project: strawberry.Parent[Project],
    ) -> ProjectAssetType | None:
        return await info.context.dl.project.export.aggregated_results_with_geometry.load(project.pk)

    @strawberry.field
    async def export_groups(self, info: Info, project: strawberry.Parent[Project]) -> ProjectAssetType | None:
        return await info.context.dl.project.export.groups.load(project.pk)

    @strawberry.field
    async def export_history(self, info: Info, project: strawberry.Parent[Project]) -> ProjectAssetType | None:
        return await info.context.dl.project.export.history.load(project.pk)

    @strawberry.field
    async def export_results(self, info: Info, project: strawberry.Parent[Project]) -> ProjectAssetType | None:
        return await info.context.dl.project.export.results.load(project.pk)

    @strawberry.field
    async def export_tasks(self, info: Info, project: strawberry.Parent[Project]) -> ProjectAssetType | None:
        return await info.context.dl.project.export.tasks.load(project.pk)

    @strawberry.field
    async def export_users(self, info: Info, project: strawberry.Parent[Project]) -> ProjectAssetType | None:
        return await info.context.dl.project.export.users.load(project.pk)

    @strawberry.field
    async def export_area_of_interest(self, info: Info, project: strawberry.Parent[Project]) -> ProjectAssetType | None:
        # TODO(tnagorra): We need to get the area of interest from aoi input project asset
        return await info.context.dl.project.export.area_of_interest.load(project.pk)

    # Find/Compare
    @strawberry.field
    async def export_hot_tasking_manager_geometries(
        self,
        info: Info,
        project: strawberry.Parent[Project],
    ) -> ProjectAssetType | None:
        return await info.context.dl.project.export.hot_tasking_manager_geometries.load(project.pk)

    @strawberry.field
    async def export_moderate_to_high_agreement_yes_maybe_geometries(
        self,
        info: Info,
        project: strawberry.Parent[Project],
    ) -> ProjectAssetType | None:
        return await info.context.dl.project.export.moderate_to_high_agreement_yes_maybe_geometries.load(project.pk)


@strawberry_django.type(Project)
class ProjectType(UserResourceTypeMixin, ProjectExportAssetTypeMixin, FirebasePushResourceTypeMixin):
    id: strawberry.ID
    project_type: strawberry.auto
    requesting_organization_id: strawberry.ID
    requesting_organization: OrganizationType
    topic: strawberry.auto
    region: strawberry.auto
    project_number: strawberry.auto
    look_for: strawberry.auto
    project_instruction: strawberry.auto
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
    required_results: strawberry.auto

    @strawberry_django.field(
        description="No. of unique contributors in this project",
    )
    def contributors_count(self) -> int:
        # TODO(tnagorra): We need to implement this
        return 0

    @strawberry_django.field(
        only=["topic", "region", "project_number", "requesting_organization__name"],
        annotate={"generated_name": Project.generate_name_query()},
        description="Project name generated from topic, region, project number, and requesting organization name.",
    )
    def name(self, project: strawberry.Parent[Project]) -> str:
        if getattr(project, "generated_name", None):
            return project.generated_name  # type: ignore[reportAttributeAccessIssue]
        # This is used for mutation response
        return project.generate_name()

    @strawberry_django.field(only=["firebase_id"])
    def website_url(self, project: strawberry.Parent[Project]) -> str:
        return Config.WebsiteKeys.project(project.firebase_id)

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
        | StreetProjectPropertyType
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
        if project.project_type_enum == Project.Type.STREET:
            return typing.cast(
                "StreetProjectPropertyType",
                street_project.StreetProjectProperty.model_validate(data),
            )
        typing.assert_never(project.project_type_enum)

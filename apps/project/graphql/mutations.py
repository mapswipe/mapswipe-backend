import strawberry
import strawberry_django
from django.utils.translation import gettext
from strawberry_django.permissions import IsAuthenticated

from apps.common.models import AssetTypeEnum
from apps.project.models import Organization, Project, ProjectAsset, ProjectAssetInputTypeEnum
from apps.project.serializers import (
    OrganizationSerializer,
    ProcessedProjectUpdateSerializer,
    ProjectAssetSerializer,
    ProjectCreateSerializer,
    ProjectStatusUpdateSerializer,
    ProjectUpdateSerializer,
)
from main.graphql.context import Info
from utils.graphql.mutations import ModelMutation
from utils.graphql.types import CustomErrorType, MutationResponseType

from .inputs.inputs import (
    OrganizationCreateInput,
    OrganizationUpdateInput,
    ProcessedProjectUpdateInput,
    ProjectAssetCreateInput,
    ProjectCreateInput,
    ProjectStatusUpdateInput,
    ProjectUpdateInput,
)
from .types.types import OrganizationType, ProjectAssetsDeleteType, ProjectAssetType, ProjectType


@strawberry.type
class Mutation:
    delete_project: ProjectType = strawberry_django.mutations.delete(extensions=[IsAuthenticated()])

    @strawberry_django.mutation(extensions=[IsAuthenticated()])
    async def create_project(self, info: Info, data: ProjectCreateInput) -> MutationResponseType[ProjectType]:
        return await ModelMutation(ProjectCreateSerializer).handle_create_mutation(data, info, None)

    @strawberry_django.mutation(extensions=[IsAuthenticated()])
    async def update_project(
        self,
        info: Info,
        data: ProjectUpdateInput,
        pk: strawberry.ID,
    ) -> MutationResponseType[ProjectType]:
        project = await Project.objects.aget(pk=pk)
        return await ModelMutation(ProjectUpdateSerializer).handle_update_mutation(data, info, project)

    @strawberry_django.mutation(extensions=[IsAuthenticated()])
    async def update_processed_project(
        self,
        info: Info,
        data: ProcessedProjectUpdateInput,
        pk: strawberry.ID,
    ) -> MutationResponseType[ProjectType]:
        project = await Project.objects.aget(pk=pk)
        return await ModelMutation(ProcessedProjectUpdateSerializer).handle_update_mutation(data, info, project)

    @strawberry_django.mutation(extensions=[IsAuthenticated()])
    async def create_project_asset(
        self,
        info: Info,
        data: ProjectAssetCreateInput,
    ) -> MutationResponseType[ProjectAssetType]:
        return await ModelMutation(ProjectAssetSerializer).handle_create_mutation(data, info, None)

    @strawberry_django.mutation(extensions=[IsAuthenticated()])
    async def create_organization(
        self,
        info: Info,
        data: OrganizationCreateInput,
    ) -> MutationResponseType[OrganizationType]:
        return await ModelMutation(OrganizationSerializer).handle_create_mutation(data, info, None)

    @strawberry_django.mutation(extensions=[IsAuthenticated()])
    async def update_organization(
        self,
        info: Info,
        data: OrganizationUpdateInput,
        pk: strawberry.ID,
    ) -> MutationResponseType[OrganizationType]:
        organization = await Organization.objects.aget(pk=pk)
        return await ModelMutation(OrganizationSerializer).handle_update_mutation(data, info, organization)

    @strawberry_django.mutation(extensions=[IsAuthenticated()])
    async def update_project_status(
        self,
        info: Info,
        data: ProjectStatusUpdateInput,
        pk: strawberry.ID,
    ) -> MutationResponseType[ProjectType]:
        project = await Project.objects.aget(pk=pk)
        return await ModelMutation(ProjectStatusUpdateSerializer).handle_update_mutation(data, info, project)

    @strawberry_django.mutation(extensions=[IsAuthenticated()])
    async def delete_project_assets(
        self,
        info: Info,
        project_id: strawberry.ID,
        asset_input_type: list[ProjectAssetInputTypeEnum],
    ) -> MutationResponseType[ProjectAssetsDeleteType]:
        project = await Project.objects.aget(pk=project_id)

        if project.status_enum not in [Project.Status.DRAFT, Project.Status.PROCESSING_FAILED]:
            return MutationResponseType(
                ok=False,
                errors=CustomErrorType(
                    {
                        "array_errors": None,
                        "client_id": project.client_id,
                        "field": "nonFieldErrors",
                        "messages": gettext("Cannot delete assets of project with status %s") % project.status_enum.label,
                    },
                ),
                result=None,
            )

        deleted_count = await (
            ProjectAsset.usable_objects()
            .filter(
                project_id=project_id,
                type=AssetTypeEnum.INPUT,
                input_type__in=asset_input_type,
            )
            .aupdate(marked_as_deleted=True)
        )

        return MutationResponseType(
            ok=True,
            errors=None,
            result=ProjectAssetsDeleteType(
                count=deleted_count,
            ),
        )

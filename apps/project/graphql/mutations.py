import strawberry
import strawberry_django
from strawberry_django.permissions import IsAuthenticated

from apps.project.models import Organization, Project
from apps.project.serializers import (
    OrganizationSerializer,
    ProcessedProjectSerializer,
    ProjectAssetSerializer,
    ProjectCreateSerializer,
    ProjectUpdateSerializer,
)
from main.graphql.context import Info
from utils.graphql.mutations import ModelMutation
from utils.graphql.types import MutationResponseType

from .inputs import (
    OrganizationCreateInput,
    OrganizationUpdateInput,
    ProcessedProjectUpdateInput,
    ProjectAssetCreateInput,
    ProjectCreateInput,
    ProjectUpdateInput,
)
from .types import OrganizationType, ProjectAssetType, ProjectType


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
        return await ModelMutation(ProcessedProjectSerializer).handle_update_mutation(data, info, project)

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

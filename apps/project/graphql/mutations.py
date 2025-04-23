import strawberry
import strawberry_django
from strawberry_django.permissions import IsAuthenticated

from apps.project.models import Project
from apps.project.serializers import ProcessedProjectSerializer, ProjectSerializer
from main.graphql.context import Info
from utils.graphql.mutations import ModelMutation
from utils.graphql.types import MutationResponseType

from .inputs import ProcessedProjectUpdateInput, ProjectCreateInput, ProjectUpdateInput
from .types import ProjectType


@strawberry.type
class Mutation:
    delete_project: ProjectType = strawberry_django.mutations.delete(extensions=[IsAuthenticated()])

    @strawberry_django.mutation(extensions=[IsAuthenticated()])
    async def create_project(self, info: Info, data: ProjectCreateInput) -> MutationResponseType[ProjectType]:
        return await ModelMutation(ProjectSerializer).handle_create_mutation(data, info, None)

    @strawberry_django.mutation(extensions=[IsAuthenticated()])
    async def update_project(
        self,
        info: Info,
        data: ProjectUpdateInput,
        pk: strawberry.ID,
    ) -> MutationResponseType[ProjectType]:
        project = await Project.objects.aget(pk=pk)
        return await ModelMutation(ProjectSerializer).handle_update_mutation(data, info, project)

    @strawberry_django.mutation(extensions=[IsAuthenticated()])
    async def update_processed_project(
        self,
        info: Info,
        data: ProcessedProjectUpdateInput,
        pk: strawberry.ID,
    ) -> MutationResponseType[ProjectType]:
        project = await Project.objects.aget(pk=pk)
        return await ModelMutation(ProcessedProjectSerializer).handle_update_mutation(data, info, project)

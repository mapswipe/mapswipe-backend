import strawberry
import strawberry_django
from strawberry_django.permissions import IsAuthenticated

from apps.project.serializers import ProjectSerializer
from main.graphql.context import Info
from utils.graphql.mutations import ModelMutation
from utils.graphql.types import MutationResponseType

from .inputs import ProjectInput, ProjectInputPartial
from .types import ProjectType


@strawberry.type
class Mutation:
    update_project: ProjectType = strawberry_django.mutations.update(ProjectInputPartial, extensions=[IsAuthenticated()])
    delete_project: ProjectType = strawberry_django.mutations.delete(extensions=[IsAuthenticated()])

    @strawberry_django.mutation(extensions=[IsAuthenticated()])
    async def create_project(self, info: Info, data: ProjectInput) -> MutationResponseType[ProjectType]:
        return await ModelMutation(ProjectSerializer).handle_create_mutation(data, info, None)

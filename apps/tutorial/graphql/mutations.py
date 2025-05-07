import strawberry
import strawberry_django
from strawberry_django.permissions import IsAuthenticated

from apps.tutorial.models import Tutorial
from apps.tutorial.serializers import TutorialSerializer
from main.graphql.context import Info
from utils.graphql.mutations import ModelMutation
from utils.graphql.types import MutationResponseType

from .inputs import TutorialCreateInput, TutorialUpdateInput
from .types import TutorialType


@strawberry.type
class Mutation:
    delete_tutorial: TutorialType = strawberry_django.mutations.delete(extensions=[IsAuthenticated()])

    @strawberry_django.mutation(extensions=[IsAuthenticated()])
    async def create_tutorial(self, info: Info, data: TutorialCreateInput) -> MutationResponseType[TutorialType]:
        return await ModelMutation(TutorialSerializer).handle_create_mutation(data, info, None)

    @strawberry_django.mutation(extensions=[IsAuthenticated()])
    async def update_tutorial(
        self,
        info: Info,
        data: TutorialUpdateInput,
        pk: strawberry.ID,
    ) -> MutationResponseType[TutorialType]:
        tutorial = await Tutorial.objects.aget(pk=pk)
        # TODO(tnagorra):
        # 1. Add a function to update nested update mutations
        # 2. Remove deletes
        return await ModelMutation(TutorialSerializer).handle_update_mutation(
            data,
            info,
            tutorial,
        )

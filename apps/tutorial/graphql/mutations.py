import strawberry
import strawberry_django
from strawberry_django.permissions import IsAuthenticated

from apps.tutorial.models import (
    Tutorial,
    TutorialInformationPage,
    TutorialInformationPageBlock,
    TutorialScenarioPage,
    TutorialTask,
)
from apps.tutorial.serializers import TutorialSerializer
from main.graphql.context import Info
from utils.graphql.common import DataclassInstance
from utils.graphql.mutations import ModelMutation
from utils.graphql.types import CudInput, MutationResponseType

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

        # NOTE: Remove all deletions
        def transformer(obj: DataclassInstance):
            if not isinstance(obj, CudInput):
                return (False, obj)

            if obj.delete is not None and obj.delete != strawberry.UNSET:
                return (True, None)

            if obj.create is not None and obj.create != strawberry.UNSET:
                return (True, obj.create)

            if obj.update is not None and obj.update != strawberry.UNSET:
                return (True, obj.update)

            return (False, obj)

        for scenario in data.scenarios or []:
            if scenario.delete is not None and scenario.delete != strawberry.UNSET:
                await TutorialScenarioPage.objects.filter(id=scenario.delete.id).adelete()
                continue
            if scenario.update is not None and scenario.update != strawberry.UNSET:
                for task in scenario.update.tasks or []:
                    if task.delete is not None and task.delete != strawberry.UNSET:
                        await TutorialTask.objects.filter(id=task.delete.id).adelete()
        for information_page in data.information_pages or []:
            if information_page.delete is not None and information_page.delete != strawberry.UNSET:
                await TutorialInformationPage.objects.filter(id=information_page.delete.id).adelete()
                continue
            if information_page.update is not None and information_page.update != strawberry.UNSET:
                for block in information_page.update.blocks or []:
                    if block.delete is not None and block.delete != strawberry.UNSET:
                        await TutorialInformationPageBlock.objects.filter(id=block.delete.id).adelete()

        return await ModelMutation(TutorialSerializer).handle_update_mutation(
            data,
            info,
            tutorial,
            None,
            transformer,
        )

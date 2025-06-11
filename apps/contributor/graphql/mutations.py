import strawberry
import strawberry_django
from strawberry_django.permissions import IsAuthenticated

from apps.contributor.models import ContributorUserGroup
from apps.contributor.serializers import (
    ContributorUserGroupSerializer,
)
from main.graphql.context import Info
from utils.graphql.mutations import ModelMutation
from utils.graphql.types import MutationResponseType

from .inputs import (
    ContributorUserGroupCreateInput,
    ContributorUserGroupUpdateInput,
)
from .types import ContributorUserGroupType


@strawberry.type
class Mutation:
    @strawberry_django.mutation(extensions=[IsAuthenticated()])
    async def create_contributor_user_group(
        self,
        info: Info,
        data: ContributorUserGroupCreateInput,
    ) -> MutationResponseType[ContributorUserGroupType]:
        return await ModelMutation(ContributorUserGroupSerializer).handle_create_mutation(data, info, None)

    @strawberry_django.mutation(extensions=[IsAuthenticated()])
    async def update_contributor_user_group(
        self,
        info: Info,
        data: ContributorUserGroupUpdateInput,
        pk: strawberry.ID,
    ) -> MutationResponseType[ContributorUserGroupType]:
        contributor_user_group = await ContributorUserGroup.objects.aget(pk=pk)
        return await ModelMutation(ContributorUserGroupSerializer).handle_update_mutation(data, info, contributor_user_group)

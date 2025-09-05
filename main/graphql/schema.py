import strawberry
from django.core.files.uploadedfile import UploadedFile
from strawberry.django.views import AsyncGraphQLView
from strawberry.file_uploads import Upload
from strawberry_django.optimizer import DjangoOptimizerExtension

# NOTE: We are importing monkey_patches for side-effect
# The patch is required by the following graphql imports
import utils.graphql.monkey_patches  # noqa: F401  # isort: skip # type: ignore[reportUnusedImport]
from apps.common.graphql import queries as common_queries
from apps.community_dashboard.graphql import queries as community_dashboard_queries
from apps.contributor.graphql import mutations as contributor_mutations
from apps.contributor.graphql import queries as contributor_queries
from apps.project.graphql import mutations as project_mutations
from apps.project.graphql import queries as project_queries
from apps.tutorial.graphql import mutations as tutorial_mutations
from apps.tutorial.graphql import queries as tutorial_queries
from apps.user.graphql import mutations as user_mutations
from apps.user.graphql import queries as user_queries

from .context import GraphQLContext
from .dataloaders import GlobalDataLoader
from .enums import AppEnumCollection, AppEnumCollectionData

# from strawberry.schema.config import StrawberryConfig


class CustomAsyncGraphQLView(AsyncGraphQLView):
    async def get_context(self, *args, **kwargs) -> GraphQLContext:  # type: ignore[reportIncompatibleMethodOverride]
        return GraphQLContext(
            *args,
            **kwargs,
            dl=GlobalDataLoader(),
        )


@strawberry.type
class Query(
    common_queries.Query,
    user_queries.Query,
    project_queries.Query,
    tutorial_queries.Query,
    contributor_queries.Query,
    community_dashboard_queries.Query,
):
    enums: AppEnumCollection = strawberry.field(  # type: ignore[reportGeneralTypeIssues]
        resolver=lambda: AppEnumCollectionData(),
    )


@strawberry.type
class Mutation(
    user_mutations.Mutation,
    project_mutations.Mutation,
    tutorial_mutations.Mutation,
    contributor_mutations.Mutation,
): ...


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[
        DjangoOptimizerExtension,
    ],
    scalar_overrides={
        UploadedFile: Upload,
    },
    # config=StrawberryConfig(auto_camel_case=True)
)

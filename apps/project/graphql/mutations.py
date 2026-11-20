import logging
import typing

import strawberry
import strawberry_django
from asgiref.sync import sync_to_async
from django.utils.translation import gettext
from strawberry_django.permissions import IsAuthenticated

from apps.common.models import AssetTypeEnum
from apps.project.graphql.types.project_types.validate import (
    TestValidateAoiObjectsResponse,
    TestValidateObjectGeojsonUrlResponse,
    TestValidateTaskingManagerProjectResponse,
    ValidateTestObjectSourceResponse,
)
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
from project_types.base.project import ValidationException
from project_types.validate import object_source_checks
from utils import fields
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

logger = logging.getLogger(__name__)


@sync_to_async
def _run_object_source_test[TestResponse: ValidateTestObjectSourceResponse](
    info: Info,
    response: TestResponse,
    run_test: typing.Callable[..., object_source_checks.ObjectSourceTestResult],
    **kwargs: typing.Any,
) -> TestResponse:
    try:
        project = object_source_checks.get_testable_project(response.project_id or "")
        result = run_test(project, info.context.request.user, **kwargs)
    except ValidationException as e:
        return response.generate_error(str(e))
    except Exception:
        logger.error("Object source test failed unexpectedly", exc_info=True)
        return response.generate_error()

    response.object_count = result.object_count
    response.aoi_geometry_asset = result.aoi_geometry_asset  # type: ignore[reportAttributeAccessIssue]
    return response


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

    # NOTE: The object source tests are mutations because each test stores the AOI as a project asset
    @strawberry_django.mutation(extensions=[IsAuthenticated()])
    async def test_aoi_objects(
        self,
        info: Info,
        project_id: strawberry.ID,
        asset_id: strawberry.ID,
        ohsome_filter: str,
    ) -> TestValidateAoiObjectsResponse:
        return await _run_object_source_test(
            info,
            TestValidateAoiObjectsResponse(project_id=project_id, asset_id=asset_id, ohsome_filter=ohsome_filter),
            object_source_checks.run_aoi_geojson_file_test,
            asset_id=asset_id,
            ohsome_filter=ohsome_filter,
        )

    @strawberry_django.mutation(extensions=[IsAuthenticated()])
    async def test_tasking_manager_project(
        self,
        info: Info,
        project_id: strawberry.ID,
        hot_tm_id: fields.PydanticId,
        ohsome_filter: str,
    ) -> TestValidateTaskingManagerProjectResponse:
        return await _run_object_source_test(
            info,
            TestValidateTaskingManagerProjectResponse(
                project_id=project_id,
                hot_tm_id=hot_tm_id,
                ohsome_filter=ohsome_filter,
            ),
            object_source_checks.run_tasking_manager_test,
            hot_tm_id=hot_tm_id,
            ohsome_filter=ohsome_filter,
        )

    @strawberry_django.mutation(extensions=[IsAuthenticated()])
    async def test_object_geojson_url(
        self,
        info: Info,
        project_id: strawberry.ID,
        object_geojson_url: str,
    ) -> TestValidateObjectGeojsonUrlResponse:
        return await _run_object_source_test(
            info,
            TestValidateObjectGeojsonUrlResponse(project_id=project_id, object_geojson_url=object_geojson_url),
            object_source_checks.run_object_geojson_url_test,
            url=object_geojson_url,
        )

    # FIXME: Add a check that only OBJECT_IMAGE can be deleted
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

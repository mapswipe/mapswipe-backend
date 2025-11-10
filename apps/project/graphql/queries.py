import logging

import strawberry
import strawberry_django
from django.db.models import QuerySet
from graphql import GraphQLError
from strawberry_django.pagination import OffsetPaginated
from strawberry_django.permissions import IsAuthenticated

from apps.project.custom_options import get_custom_options
from apps.project.graphql.inputs.inputs import ProjectNameInput
from apps.project.graphql.types.project_types.validate import (
    TestValidateAoiObjectsResponse,
    TestValidateTaskingManagerProjectResponse,
)
from apps.project.models import Organization, Project, ProjectAsset, ProjectTypeEnum
from project_types.base.project import ValidationException
from project_types.validate.project import ValidateProject
from utils import fields
from utils.geo.raster_tile_server.config import RasterConfig, RasterTileServerNameEnum, RasterTileServerNameEnumWithoutCustom
from utils.geo.vector_tile_server.config import VectorConfig, VectorTileServerNameEnum, VectorTileServerNameEnumWithoutCustom

from .filters import OrganizationFilter, ProjectAssetFilter, ProjectFilter
from .orders import OrganizationOrder, ProjectAssetOrder, ProjectOrder
from .types.project_types.base import (
    CustomOptionType,
    RasterTileServersType,
    RasterTileServerType,
    VectorTileServerType,
)
from .types.types import (
    OrganizationType,
    ProjectAssetType,
    ProjectType,
)

logger = logging.getLogger(__name__)


def get_tile_servers() -> RasterTileServersType:
    def _get_raster_tile_server_type(enum: RasterTileServerNameEnumWithoutCustom):
        config = RasterConfig.get_config(enum)
        return RasterTileServerType(
            type=enum,
            label=str(enum.label),
            url=config["url"],
            credits=config["credits"],
            min_zoom=config["min_zoom"],
            max_zoom=config["max_zoom"],
        )

    def _get_vector_tile_server_type(enum: VectorTileServerNameEnumWithoutCustom):
        return VectorTileServerType(
            type=enum,
            label=str(enum.label),
            **VectorConfig.get_config(enum),
        )

    return RasterTileServersType(
        vector=[
            _get_vector_tile_server_type(VectorTileServerNameEnum.OPEN_STREET_MAP),
            _get_vector_tile_server_type(VectorTileServerNameEnum.VERSATILES),
            _get_vector_tile_server_type(VectorTileServerNameEnum.OPEN_FREE_MAP),
        ],
        raster=[
            _get_raster_tile_server_type(RasterTileServerNameEnum.BING),
            _get_raster_tile_server_type(RasterTileServerNameEnum.MAPBOX),
            # NOTE: Disabled because it's not working for 2+ years
            # _get_raster_tile_server_type(RasterTileServerNameEnum.MAXAR_STANDARD),
            # _get_raster_tile_server_type(RasterTileServerNameEnum.MAXAR_PREMIUM),
            _get_raster_tile_server_type(RasterTileServerNameEnum.ESRI),
            _get_raster_tile_server_type(RasterTileServerNameEnum.ESRI_BETA),
        ],
    )


@strawberry.type
class Query:
    @strawberry.field(extensions=[IsAuthenticated()])
    def default_custom_options(self, project_type: ProjectTypeEnum) -> list[CustomOptionType]:
        custom_options = get_custom_options(project_type=project_type)
        return [
            CustomOptionType(
                title=item["title"],
                icon=item["icon"],
                value=item["value"],
                description=item["description"],
                icon_color=item["icon_color"],
            )
            for item in custom_options
        ]

    @strawberry.field(extensions=[IsAuthenticated()])
    def test_aoi_objects(
        self,
        project_id: strawberry.ID | None,
        asset_id: strawberry.ID | None,
        ohsome_filter: str | None,
    ) -> TestValidateAoiObjectsResponse:
        response = TestValidateAoiObjectsResponse(
            project_id=project_id,
            asset_id=asset_id,
            ohsome_filter=ohsome_filter,
        )

        if project_id is None:
            return response.generate_error("project_id is required to test aoi elements")

        if asset_id is None:
            return response.generate_error("asset_id is required to test aoi elements")

        if ohsome_filter is None:
            return response.generate_error("ohsome_filter is required to test aoi elements")

        try:
            object_count = ValidateProject.test_ohsome_objects_from_aoi_asset(
                project_id,
                asset_id,
                ohsome_filter,
            )

            response.object_count = object_count
            return response
        except ValidationException as e:
            return response.generate_error(str(e))
        except Exception as e:
            raise GraphQLError(str(e)) from e

    @strawberry.field(extensions=[IsAuthenticated()])
    def test_tasking_manager_project(
        self,
        hot_tm_id: fields.PydanticId | None,
        ohsome_filter: str | None,
    ) -> TestValidateTaskingManagerProjectResponse:
        response = TestValidateTaskingManagerProjectResponse(
            hot_tm_id=hot_tm_id,
            ohsome_filter=ohsome_filter,
        )

        if hot_tm_id is None:
            return response.generate_error("hot_tm_id is required to test HOT project aoi elements")

        if ohsome_filter is None:
            return response.generate_error("ohsome_filter is required to test HOT project aoi elements")

        try:
            object_count = ValidateProject.test_tasking_manager_project(
                hot_tm_id,
                ohsome_filter,
            )

            response.object_count = object_count

            return response
        except ValidationException as e:
            return response.generate_error(str(e))
        except Exception as e:
            raise GraphQLError(str(e)) from e

    tile_servers: RasterTileServersType = strawberry.field(resolver=get_tile_servers, extensions=[IsAuthenticated()])

    # Private --------------------
    project: ProjectType = strawberry_django.field(extensions=[IsAuthenticated()])
    public_project: ProjectType = strawberry_django.field()

    project_asset: ProjectAssetType = strawberry_django.field(extensions=[IsAuthenticated()])

    # --- Paginated
    # FIXME: add description of include_all using Annotated
    @strawberry_django.offset_paginated(
        OffsetPaginated[ProjectAssetType],
        order=ProjectAssetOrder,
        filters=ProjectAssetFilter,
        extensions=[IsAuthenticated()],
    )
    def project_assets(
        self,
        include_all: bool = False,
    ) -> QuerySet[ProjectAsset]:
        if include_all:
            return ProjectAsset.objects.all()
        return ProjectAsset.usable_objects()

    organization: OrganizationType = strawberry_django.field(extensions=[IsAuthenticated()])
    public_organization: OrganizationType = strawberry_django.field()

    # --- Paginated
    @strawberry_django.offset_paginated(
        OffsetPaginated[OrganizationType],
        order=OrganizationOrder,
        filters=OrganizationFilter,
        extensions=[IsAuthenticated()],
    )
    # TODO: We need attribute description `include_all` visible in graphiql
    def organizations(
        self,
        include_all: bool = False,
    ) -> QuerySet[Organization]:
        if include_all:
            return Organization.objects.all()
        return Organization.objects.exclude(is_archived=True).all()

    @strawberry_django.offset_paginated(
        OffsetPaginated[OrganizationType],
        order=OrganizationOrder,
        filters=OrganizationFilter,
    )
    def public_organizations(
        self,
    ) -> QuerySet[Organization]:
        return Organization.objects.exclude(is_archived=True).all()

    # --- Paginated
    @strawberry_django.offset_paginated(
        OffsetPaginated[ProjectType],
        order=ProjectOrder,
        filters=ProjectFilter,
        extensions=[IsAuthenticated()],
    )
    # TODO: We need attribute description `include_all` visible in graphiql
    def projects(
        self,
        include_all: bool = False,
    ) -> QuerySet[Project]:
        if include_all:
            return Project.objects.all()
        return Project.objects.filter(
            status__in=[
                Project.Status.PROCESSED,
                Project.Status.PUBLISHED,
                Project.Status.PAUSED,
            ],
        ).all()

    @strawberry_django.offset_paginated(
        OffsetPaginated[ProjectType],
        order=ProjectOrder,
        filters=ProjectFilter,
    )
    def public_projects(
        self,
    ) -> QuerySet[Project]:
        return Project.objects.filter(
            status__in=[
                Project.Status.PUBLISHED,
                Project.Status.PAUSED,
                Project.Status.FINISHED,
            ],
        ).all()

    # NOTE: This query is only for name hint.
    @strawberry_django.field()
    def project_name(
        self,
        params: ProjectNameInput | None,
    ) -> str:
        if not params:
            raise GraphQLError("params is required to build project name")
        requesting_organization = Organization.objects.get(pk=params.requesting_organization_id)

        return Project.generate_project_name(
            project_type=params.project_type,
            topic=params.topic,
            requesting_organization_name=requesting_organization.name,
            region=params.region,
            project_number=params.project_number,
        )

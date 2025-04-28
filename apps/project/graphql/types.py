import typing

import strawberry
import strawberry_django

from apps.common.graphql.types import UserResourceTypeMixin
from apps.project.models import Organization, Project, ProjectAsset
from apps.project.project_types.tile_map_service.compare import project as compare_project
from apps.project.project_types.tile_map_service.completeness import project as completeness_project
from apps.project.project_types.tile_map_service.find import project as find_project
from utils.geo.tile_server.models import TileServerCommonConfig, TileServerConfig, TileServerCustomConfig


def prepare_tile_server_property(prop: dict | None):
    # FIXME(tnagorra): Do we need to do a deep clone?
    if prop is None:
        return None

    custom = prop.pop("custom", None)
    bing = prop.pop("bing", None)
    mapbox = prop.pop("mapbox", None)
    maxar_standard = prop.pop("maxar_standard", None)
    maxar_premium = prop.pop("maxar_premium", None)
    esri = prop.pop("esri", None)
    esri_beta = prop.pop("esri_beta", None)

    return ProjectTileServerConfig(
        **prop,
        custom=ProjectTileServerCustomConfig(**custom) if custom is not None else None,
        bing=ProjectTileServerCommonConfig(**bing) if bing is not None else None,
        mapbox=ProjectTileServerCommonConfig(**mapbox) if mapbox is not None else None,
        maxar_standard=ProjectTileServerCommonConfig(**maxar_standard) if maxar_standard is not None else None,
        maxar_premium=ProjectTileServerCommonConfig(**maxar_premium) if maxar_premium is not None else None,
        esri=ProjectTileServerCommonConfig(**esri) if esri is not None else None,
        esri_beta=ProjectTileServerCommonConfig(**esri_beta) if esri_beta is not None else None,
    )


@strawberry_django.type(Organization)
class OrganizationType(UserResourceTypeMixin):
    id: strawberry.ID
    name: strawberry.auto


# Tile server
@strawberry.experimental.pydantic.type(model=TileServerCustomConfig, all_fields=True)
class ProjectTileServerCustomConfig: ...


@strawberry.experimental.pydantic.type(model=TileServerCommonConfig, all_fields=True)
class ProjectTileServerCommonConfig: ...


@strawberry.experimental.pydantic.type(model=TileServerConfig, all_fields=True)
class ProjectTileServerConfig: ...


# Project Properties
@strawberry.experimental.pydantic.type(model=compare_project.CompareProjectProperty, all_fields=True)
class CompareProjectPropertyType: ...


@strawberry.experimental.pydantic.type(model=find_project.FindProjectProperty, all_fields=True)
class FindProjectPropertyType: ...


@strawberry.experimental.pydantic.type(model=completeness_project.CompletenessProjectProperty, all_fields=True)
class CompletenessProjectPropertyType: ...


@strawberry_django.type(Project)
class ProjectType:
    id: strawberry.ID
    project_type: strawberry.auto
    requesting_organization_id: strawberry.ID
    requesting_organization: OrganizationType
    name: strawberry.auto
    look_for: strawberry.auto
    additional_info_url: strawberry.auto
    description: strawberry.auto
    # TODO(tnagorra) Add image
    # TODO(tnagorra): Add tutorial and tutorial_id
    verification_number: strawberry.auto
    group_size: strawberry.auto
    max_tasks_per_user: strawberry.auto
    is_featured: strawberry.auto
    status: strawberry.auto
    processing_status: strawberry.auto
    progress: strawberry.auto

    @strawberry_django.field(only=["project_type_specifics", "project_type"])
    async def project_type_specifics(
        self,
        project: strawberry.Parent[Project],
    ) -> CompareProjectPropertyType | FindProjectPropertyType | CompletenessProjectPropertyType | None:
        data = project.project_type_specifics
        if data is None:
            return None
        if project.project_type_enum == Project.Type.FIND:
            tile_server_property = data.pop("tile_server_property")
            return FindProjectPropertyType(
                **data,
                tile_server_property=prepare_tile_server_property(tile_server_property),
            )
        if project.project_type_enum == Project.Type.COMPARE:
            tile_server_property = data.pop("tile_server_property")
            tile_server_b_property = data.pop("tile_server_b_property")
            return CompareProjectPropertyType(
                **data,
                tile_server_property=prepare_tile_server_property(tile_server_property),
                tile_server_b_property=prepare_tile_server_property(tile_server_b_property),
            )
        if project.project_type_enum == Project.Type.COMPLETENESS:
            tile_server_property = data.pop("tile_server_property")
            tile_server_b_property = data.pop("tile_server_b_property")
            return CompletenessProjectPropertyType(
                **data,
                tile_server_property=prepare_tile_server_property(tile_server_property),
                tile_server_b_property=prepare_tile_server_property(tile_server_b_property),
            )
        typing.assert_never(project.project_type_enum)


@strawberry_django.type(ProjectAsset)
class ProjectAssetType:
    id: strawberry.ID
    type: strawberry.auto
    mimetype: strawberry.auto
    project_id: strawberry.ID

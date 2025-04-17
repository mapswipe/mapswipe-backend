import strawberry
import strawberry_django

from apps.common.graphql.types import UserResourceTypeMixin
from apps.project.models import Organization, Project
from apps.project.project_types.tile_map_service.compare import project as compare_project
from apps.project.project_types.tile_map_service.find import project as find_project
from utils.geo.tile_server.models import TileServerCommonConfig, TileServerConfig, TileServerCustomConfig


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


@strawberry_django.type(Project)
class ProjectType:
    id: strawberry.ID
    name: strawberry.auto

    organization_id: strawberry.ID
    organization: OrganizationType
    project_type: strawberry.auto

    project_type_specifics: CompareProjectPropertyType | FindProjectPropertyType

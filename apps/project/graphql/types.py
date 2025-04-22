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
    project_type_specifics: CompareProjectPropertyType | FindProjectPropertyType
    # TODO(tnagorra): Add aoi_geometry_file
    is_featured: strawberry.auto
    status: strawberry.auto
    progress: strawberry.auto
    # TODO(tnagorra): Add processed_geometry_file

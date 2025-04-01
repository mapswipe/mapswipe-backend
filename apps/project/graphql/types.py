import typing

import strawberry
import strawberry_django

from apps.common.graphql.types import UserResourceTypeMixin
from apps.project.project_types.tile_map_service.change_detection import project as change_detection_project
from apps.project.project_types.tile_map_service.classification import project as classification_project
from utils.geo.tile_server.models import TileServerCommonConfig, TileServerConfig, TileServerCustomConfig

from ..models import Organization, Project


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
@strawberry.experimental.pydantic.type(model=change_detection_project.ChangeDetectionProjectProperty, all_fields=True)
class ChangeDetectionProjectPropertyType: ...


@strawberry.experimental.pydantic.type(model=classification_project.ClassificationProjectProperty, all_fields=True)
class ClassificationProjectPropertyType: ...


ProjectTypeSpecificAlias: typing.TypeAlias = ChangeDetectionProjectPropertyType | ClassificationProjectPropertyType


@strawberry_django.type(Project)
class ProjectType:
    id: strawberry.ID
    name: strawberry.auto

    organization_id: strawberry.ID
    organization: OrganizationType
    project_type: strawberry.auto

    project_type_specifics: ProjectTypeSpecificAlias

import typing

import strawberry
import strawberry_django

from apps.common.graphql.types import UserResourceTypeMixin
from apps.project.models import Organization, Project, ProjectAsset
from apps.project.project_types.tile_map_service.compare import project as compare_project
from apps.project.project_types.tile_map_service.completeness import project as completeness_project
from apps.project.project_types.tile_map_service.find import project as find_project
from apps.tutorial.graphql.types import TutorialType
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


@strawberry.experimental.pydantic.type(model=completeness_project.CompletenessProjectProperty, all_fields=True)
class CompletenessProjectPropertyType: ...


@strawberry_django.type(ProjectAsset)
class ProjectAssetType(UserResourceTypeMixin):
    id: strawberry.ID
    type: strawberry.auto
    file: strawberry.auto
    mimetype: strawberry.auto
    project_id: strawberry.ID
    marked_as_deleted: strawberry.auto


@strawberry_django.type(Project)
class ProjectType(UserResourceTypeMixin):
    id: strawberry.ID
    project_type: strawberry.auto
    requesting_organization_id: strawberry.ID
    requesting_organization: OrganizationType
    name: strawberry.auto
    look_for: strawberry.auto
    additional_info_url: strawberry.auto
    description: strawberry.auto
    image: ProjectAssetType | None
    tutorial: TutorialType | None
    tutorial_id: strawberry.ID | None
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
            return typing.cast("FindProjectPropertyType", find_project.FindProjectProperty.model_validate(data))
        if project.project_type_enum == Project.Type.COMPARE:
            return typing.cast("CompareProjectPropertyType", compare_project.CompareProjectProperty.model_validate(data))
        if project.project_type_enum == Project.Type.COMPLETENESS:
            return typing.cast(
                "CompletenessProjectPropertyType",
                completeness_project.CompletenessProjectProperty.model_validate(data),
            )
        typing.assert_never(project.project_type_enum)

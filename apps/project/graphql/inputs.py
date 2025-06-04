import strawberry
import strawberry_django
from strawberry.file_uploads import Upload

from apps.common.graphql.inputs import (
    UserResourceCreateInputMixin,
    UserResourceTopLevelUpdateInputMixin,
)
from apps.project.models import Organization, Project, ProjectAsset
from apps.project.project_types.tile_map_service.compare import project as compare_project
from apps.project.project_types.tile_map_service.completeness import project as completeness_project
from apps.project.project_types.tile_map_service.find import project as find_project
from apps.project.project_types.validate import project as validate_project
from utils.geo.tile_server.models import TileServerCommonConfig, TileServerConfig, TileServerCustomConfig


# Tile server
@strawberry.experimental.pydantic.input(model=TileServerCustomConfig, all_fields=True)
class TileServerCustomConfigInput: ...


@strawberry.experimental.pydantic.input(model=TileServerCommonConfig, all_fields=True)
class TileServerCommonConfigInput: ...


@strawberry.experimental.pydantic.input(model=TileServerConfig, all_fields=True)
class ProjectTileServerConfigInput: ...


@strawberry.experimental.pydantic.input(model=completeness_project.VectorTileServerConfig, all_fields=True)
class ProjectVectorTileServerConfigInput: ...


@strawberry.experimental.pydantic.input(model=completeness_project.OverlayTileServerConfig, all_fields=True)
class ProjectOverlayTileServerConfigInput:
    raster: TileServerConfig | None = strawberry.UNSET
    vector: completeness_project.VectorTileServerConfig | None = strawberry.UNSET


@strawberry.experimental.pydantic.input(model=validate_project.ValidateObjectSourceConfig, all_fields=True)
class ValidateObjectSourceConfigInput: ...


# Project Properties
@strawberry.experimental.pydantic.input(model=compare_project.CompareProjectProperty, all_fields=True)
class CompareProjectPropertyInput: ...


@strawberry.experimental.pydantic.input(model=find_project.FindProjectProperty, all_fields=True)
class FindProjectPropertyInput: ...


@strawberry.experimental.pydantic.input(model=completeness_project.CompletenessProjectProperty, all_fields=True)
class CompletenessProjectPropertyInput: ...


@strawberry.experimental.pydantic.input(model=validate_project.ValidateProjectProperty, all_fields=True)
class ValidateProjectPropertyInput: ...


@strawberry_django.input(Organization)
class OrganizationCreateInput(UserResourceCreateInputMixin):
    name: strawberry.auto


@strawberry_django.input(Organization)
class OrganizationUpdateInput(UserResourceTopLevelUpdateInputMixin):
    name: strawberry.auto


@strawberry.input(one_of=True)
class ProjectTypeSpecificInput:
    compare: CompareProjectPropertyInput | None = strawberry.UNSET
    find: FindProjectPropertyInput | None = strawberry.UNSET
    completeness: CompletenessProjectPropertyInput | None = strawberry.UNSET
    validate: ValidateProjectPropertyInput | None = strawberry.UNSET


# NOTE: Make sure this matches with the serializers ../serializers.py
@strawberry_django.input(Project)
class ProjectCreateInput(UserResourceCreateInputMixin):
    project_type: strawberry.auto
    requesting_organization: strawberry.ID
    name: strawberry.auto
    look_for: strawberry.auto
    additional_info_url: strawberry.auto
    description: strawberry.auto


# NOTE: Make sure this matches with the serializers ../serializers.py
@strawberry_django.partial(Project)
class ProjectUpdateInput(UserResourceTopLevelUpdateInputMixin):
    name: strawberry.auto
    look_for: strawberry.auto
    additional_info_url: strawberry.auto
    description: strawberry.auto
    verification_number: strawberry.auto
    group_size: strawberry.auto
    max_tasks_per_user: strawberry.auto
    status: strawberry.auto
    tutorial: strawberry.ID | None = strawberry.UNSET
    requesting_organization: strawberry.ID | None = strawberry.UNSET
    image: strawberry.ID | None = strawberry.UNSET
    project_type_specifics: ProjectTypeSpecificInput | None = strawberry.UNSET


# NOTE: Make sure this matches with the serializers ../serializers.py
@strawberry_django.partial(Project)
class ProcessedProjectUpdateInput(UserResourceTopLevelUpdateInputMixin):
    name: strawberry.auto
    look_for: strawberry.auto
    additional_info_url: strawberry.auto
    description: strawberry.auto
    status: strawberry.auto
    tutorial: strawberry.ID | None = strawberry.UNSET
    requesting_organization: strawberry.ID | None = strawberry.UNSET
    image: strawberry.ID | None = strawberry.UNSET


# NOTE: Make sure this matches with the serializers ../serializers.py
@strawberry_django.input(ProjectAsset)
class ProjectAssetCreateInput(UserResourceCreateInputMixin):
    mimetype: strawberry.auto
    file: Upload
    project: strawberry.ID

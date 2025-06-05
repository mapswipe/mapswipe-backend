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
from utils.geo.tile_server.models import (
    TileServerCommonConfig,
    TileServerConfig,
    TileServerCustomConfig,
    VectorTileServerCommonConfig,
    VectorTileServerConfig,
    VectorTileServerCustomConfig,
)


# Organization
@strawberry_django.input(Organization)
class OrganizationCreateInput(UserResourceCreateInputMixin):
    name: strawberry.auto


@strawberry_django.input(Organization)
class OrganizationUpdateInput(UserResourceTopLevelUpdateInputMixin):
    name: strawberry.auto


# Tile server
@strawberry.experimental.pydantic.input(model=TileServerCustomConfig, all_fields=True)
class TileServerCustomConfigInput: ...


@strawberry.experimental.pydantic.input(model=TileServerCommonConfig, all_fields=True)
class TileServerCommonConfigInput: ...


# FIXME(tnagorra): Add one_of here?
@strawberry.experimental.pydantic.input(model=TileServerConfig, all_fields=True)
class ProjectTileServerConfigInput: ...


# Vector tile server
@strawberry.experimental.pydantic.input(model=VectorTileServerCustomConfig, all_fields=True)
class VectorTileServerCustomConfigInput: ...


@strawberry.experimental.pydantic.input(model=VectorTileServerCommonConfig, all_fields=True)
class VectorTileServerCommonConfigInput: ...


# FIXME(tnagorra): Add one_of here?
@strawberry.experimental.pydantic.input(model=VectorTileServerConfig, all_fields=True)
class ProjectVectorTileServerConfigInput: ...


# Project Properties: Compare
@strawberry.experimental.pydantic.input(model=compare_project.CompareProjectProperty, all_fields=True)
class CompareProjectPropertyInput: ...


# Project Properties: Find
@strawberry.experimental.pydantic.input(model=find_project.FindProjectProperty, all_fields=True)
class FindProjectPropertyInput: ...


# Project Properties: Validate
@strawberry.experimental.pydantic.input(model=validate_project.ValidateObjectSourceConfig, all_fields=True)
class ValidateObjectSourceConfigInput: ...


# FIXME(tnagorra): Add one_of here?
@strawberry.experimental.pydantic.input(model=validate_project.ValidateProjectProperty, all_fields=True)
class ValidateProjectPropertyInput: ...


# Project Properties: Completeness
@strawberry.experimental.pydantic.input(model=completeness_project.OverlayVectorTileServerConfig, all_fields=True)
class ProjectOverlayVectorTileServerConfigInput: ...


@strawberry.experimental.pydantic.input(model=completeness_project.OverlayRasterTileServerConfig, all_fields=True)
class ProjectOverlayRasterTileServerConfigInput: ...


# FIXME(tnagorra): Add one_of here?
@strawberry.experimental.pydantic.input(model=completeness_project.OverlayTileServerConfig, all_fields=True)
class ProjectOverlayTileServerConfigInput:
    raster: TileServerConfig | None = strawberry.UNSET
    vector: completeness_project.OverlayVectorTileServerConfig | None = strawberry.UNSET


@strawberry.experimental.pydantic.input(model=completeness_project.CompletenessProjectProperty, all_fields=True)
class CompletenessProjectPropertyInput: ...


# Project Properties
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

import strawberry
import strawberry_django
from strawberry.file_uploads import Upload

from apps.project.models import Project
from apps.project.project_types.tile_map_service.compare import project as compare_project
from apps.project.project_types.tile_map_service.find import project as find_project
from utils.geo.tile_server.models import TileServerCommonConfig, TileServerConfig, TileServerCustomConfig


# Tile server
@strawberry.experimental.pydantic.input(model=TileServerCustomConfig, all_fields=True)
class TileServerCustomConfigInput: ...


@strawberry.experimental.pydantic.input(model=TileServerCommonConfig, all_fields=True)
class TileServerCommonConfigInput: ...


@strawberry.experimental.pydantic.input(model=TileServerConfig, all_fields=True)
class ProjectTileServerConfigInput: ...


# Project Properties
@strawberry.experimental.pydantic.input(model=compare_project.CompareProjectProperty, all_fields=True)
class CompareProjectPropertyInput: ...


@strawberry.experimental.pydantic.input(model=find_project.FindProjectProperty, all_fields=True)
class FindProjectPropertyInput: ...


@strawberry.input(one_of=True)
class ProjectTypeSpecificInput:
    compare: CompareProjectPropertyInput | None = strawberry.UNSET
    find: FindProjectPropertyInput | None = strawberry.UNSET


# NOTE: Make sure this matches with the serializers ../serializers.py
@strawberry_django.input(Project)
class ProjectCreateInput:
    project_type: strawberry.auto
    requesting_organization: strawberry.ID
    name: strawberry.auto
    look_for: strawberry.auto
    additional_info_url: strawberry.auto
    description: strawberry.auto
    image: Upload


# NOTE: Make sure this matches with the serializers ../serializers.py
@strawberry_django.partial(Project)
class ProjectUpdateInput:
    name: strawberry.auto
    look_for: strawberry.auto
    additional_info_url: strawberry.auto
    description: strawberry.auto
    # TODO(tnagorra): Add tutorial
    verification_number: strawberry.auto
    group_size: strawberry.auto
    max_tasks_per_user: strawberry.auto
    status: strawberry.auto
    requesting_organization: strawberry.ID | None = strawberry.UNSET
    image: Upload | None = strawberry.UNSET
    project_type_specifics: ProjectTypeSpecificInput | None = strawberry.UNSET


# NOTE: Make sure this matches with the serializers ../serializers.py
@strawberry_django.partial(Project)
class ProcessedProjectUpdateInput:
    name: strawberry.auto
    look_for: strawberry.auto
    additional_info_url: strawberry.auto
    description: strawberry.auto
    # TODO(tnagorra): Add tutorial
    status: strawberry.auto
    requesting_organization: strawberry.ID | None = strawberry.UNSET
    image: Upload | None = strawberry.UNSET

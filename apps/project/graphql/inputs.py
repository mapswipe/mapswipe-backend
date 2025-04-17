import strawberry
import strawberry_django
from strawberry.file_uploads import Upload

from apps.project.models import Project
from apps.project.project_types.tile_map_service.change_detection import project as change_detection_project
from apps.project.project_types.tile_map_service.classification import project as classification_project
from utils.geo.tile_server.models import TileServerCommonConfig, TileServerConfig, TileServerCustomConfig


# Tile server
@strawberry.experimental.pydantic.input(model=TileServerCustomConfig, all_fields=True)
class TileServerCustomConfigInput: ...


@strawberry.experimental.pydantic.input(model=TileServerCommonConfig, all_fields=True)
class TileServerCommonConfigInput: ...


@strawberry.experimental.pydantic.input(model=TileServerConfig, all_fields=True)
class ProjectTileServerConfigInput: ...


# Project Properties
@strawberry.experimental.pydantic.input(model=change_detection_project.ChangeDetectionProjectProperty, all_fields=True)
class ChangeDetectionProjectPropertyInput: ...


@strawberry.experimental.pydantic.input(model=classification_project.ClassificationProjectProperty, all_fields=True)
class ClassificationProjectPropertyInput: ...


@strawberry.input(one_of=True)
class ProjectTypeSpecificInput:
    change_detection: ChangeDetectionProjectPropertyInput | None = strawberry.UNSET
    classification: ClassificationProjectPropertyInput | None = strawberry.UNSET


# NOTE: Make sure this matches with the serializers ../serializers.py
@strawberry_django.input(Project)
class ProjectInput:
    name: strawberry.auto
    project_type: strawberry.auto
    organization: strawberry.ID
    image: Upload
    geometry_file: Upload

    group_size: strawberry.auto
    verification_number: strawberry.auto
    look_for: strawberry.auto

    project_type_specifics: ProjectTypeSpecificInput


@strawberry_django.partial(Project)
class ProjectInputPartial:
    name: strawberry.auto
    project_type: strawberry.auto
    organization: strawberry.ID
    image: Upload
    geometry_file: Upload

    group_size: strawberry.auto
    verification_number: strawberry.auto
    look_for: strawberry.auto

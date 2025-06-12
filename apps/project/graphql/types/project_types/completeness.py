import strawberry

from project_types.tile_map_service.completeness import project as completeness_project

# NOTE: We are importing base just for side-effect
from . import base  # type: ignore[reportUnusedImport]  # noqa: F401


@strawberry.experimental.pydantic.type(model=completeness_project.OverlayVectorTileServerConfig, all_fields=True)
class ProjectOverlayVectorTileServerConfig: ...


@strawberry.experimental.pydantic.type(model=completeness_project.OverlayRasterTileServerConfig, all_fields=True)
class ProjectOverlayRasterTileServerConfig: ...


@strawberry.experimental.pydantic.type(model=completeness_project.OverlayTileServerConfig, all_fields=True)
class ProjectOverlayTileServerConfig: ...


@strawberry.experimental.pydantic.type(model=completeness_project.CompletenessProjectProperty, all_fields=True)
class CompletenessProjectPropertyType: ...

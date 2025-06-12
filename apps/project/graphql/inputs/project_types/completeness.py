import strawberry

from project_types.tile_map_service.completeness import project as completeness_project
from utils.geo.tile_server.models import TileServerConfig

# NOTE: We are importing base just for side-effect
from . import base  # type: ignore[reportUnusedImport]  # noqa: F401


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

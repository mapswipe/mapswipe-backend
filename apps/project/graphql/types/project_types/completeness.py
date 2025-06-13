import strawberry

from project_types.tile_map_service.completeness import project as completeness_project


@strawberry.experimental.pydantic.type(model=completeness_project.OverlayVectorTileServerConfig, all_fields=True)
class ProjectOverlayVectorTileServerConfig: ...


@strawberry.experimental.pydantic.type(model=completeness_project.OverlayRasterTileServerConfig, all_fields=True)
class ProjectOverlayRasterTileServerConfig: ...


@strawberry.experimental.pydantic.type(model=completeness_project.OverlayTileServerConfig, all_fields=True)
class ProjectOverlayTileServerConfig: ...


@strawberry.experimental.pydantic.type(model=completeness_project.CompletenessProjectProperty, all_fields=True)
class CompletenessProjectPropertyType: ...

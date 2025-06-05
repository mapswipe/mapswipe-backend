import typing

from django.db import models
from pydantic import BaseModel

from apps.project.models import Project, ProjectTypeEnum
from apps.project.project_types.tile_map_service.base import project as base_project
from utils.geo.tile_server.models import TileServerConfig
from utils.geo.tile_server.tile_server import AvailableTileServerTypeAlias, get_tile_server


# FIXME(tnagorra): Add validations
class VectorTileServerConfig(BaseModel):
    url: str
    credits: str

    source_name: str

    fill_color: str
    fill_opacity: float

    line_color: str
    line_opacity: float
    line_width: float

    circle_color: str
    circle_opacity: float
    circle_radius: float


class OverlayLayerTypeEnum(models.TextChoices):
    VECTOR_TILE = "VECTOR_TILE", "Vector Tile"
    RASTER_TILE = "RASTER_TILE", "Raster Tile"


# FIXME(tnagorra): Add "one of" validation
# FIXME(tnagorra): Add field validations
class OverlayTileServerConfig(BaseModel):
    type: OverlayLayerTypeEnum
    raster: TileServerConfig | None = None
    vector: VectorTileServerConfig | None = None


class CompletenessProjectProperty(base_project.TileMapServiceProjectProperty):
    overlay_tile_server_property: OverlayTileServerConfig


class CompletenessProjectTaskGroupProperty(base_project.TileMapServiceProjectTaskGroupProperty): ...


class CompletenessProjectTaskProperty(base_project.TileMapServiceProjectTaskProperty):
    # NOTE: this is only required for raster layer
    url_overlay_layer: str | None = None


class CompletenessProject(
    base_project.TileMapServiceBaseProject[
        CompletenessProjectProperty,
        CompletenessProjectTaskGroupProperty,
        CompletenessProjectTaskProperty,
    ],
):
    overlay_raster_tile_server: AvailableTileServerTypeAlias | None
    overlay_vector_tile_server: VectorTileServerConfig | None

    project_property_class = CompletenessProjectProperty
    project_task_group_property_class = CompletenessProjectTaskGroupProperty
    project_task_property_class = CompletenessProjectTaskProperty

    def __init__(self, project: Project):
        super().__init__(project)
        if typing.TYPE_CHECKING:
            assert project.project_type == ProjectTypeEnum.COMPLETENESS, f"{type(self)} is defined for COMPLETENESS"

        prop = self.project_type_specifics.overlay_tile_server_property
        self.overlay_vector_tile_server = prop.vector if prop.type == OverlayLayerTypeEnum.VECTOR_TILE else None
        self.overlay_tile_server = (
            get_tile_server(prop.raster)
            if prop.type == OverlayLayerTypeEnum.RASTER_TILE and prop.raster is not None
            else None
        )

        # FIXME(tnagorra): Add this check
        # assert self.overlay_vector_tile_server is not None or self.overlay_raster_tile_server is not None,
        # f"Either vector or raster overlay should be defined"

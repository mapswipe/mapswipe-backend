import typing

from django.db import models
from pydantic import BaseModel, field_validator, model_validator

from apps.project.models import Project, ProjectTypeEnum
from apps.project.project_types.tile_map_service.base import project as base_project
from utils.geo.tile_server.models import TileServerConfig, VectorTileServerConfig
from utils.geo.tile_server.tile_server import (
    AvailableTileServerTypeAlias,
    AvailableVectorTileServerTypeAlias,
    get_tile_server,
    get_vector_tile_server,
)


class OverlayLayerTypeEnum(models.TextChoices):
    VECTOR_TILE = "VECTOR_TILE", "Vector Tile"
    RASTER_TILE = "RASTER_TILE", "Raster Tile"


# FIXME(tnagorra): Add validations
class OverlayRasterTileServerConfig(BaseModel):
    tile_server: TileServerConfig
    opacity: float


# FIXME(tnagorra): Add validations
class OverlayVectorTileServerConfig(BaseModel):
    tile_server: VectorTileServerConfig

    fill_color: str
    fill_opacity: float

    line_color: str
    line_opacity: float
    line_width: float
    line_dasharray: list[int]

    circle_color: str
    circle_opacity: float
    circle_radius: float


class OverlayTileServerConfig(BaseModel):
    type: OverlayLayerTypeEnum
    raster: OverlayRasterTileServerConfig | None = None
    vector: OverlayVectorTileServerConfig | None = None

    @field_validator("type", mode="before")
    def ensure_name_enum(cls, value: str | OverlayLayerTypeEnum | None):
        if isinstance(value, str):
            return OverlayLayerTypeEnum(value)
        return value

    @model_validator(mode="after")
    def check_valid_data(self) -> typing.Self:
        match self.type:
            case OverlayLayerTypeEnum.VECTOR_TILE:
                if self.vector is None:
                    raise ValueError("vector tile config is required")
                return self
            case OverlayLayerTypeEnum.RASTER_TILE:
                if self.raster is None:
                    raise ValueError("raster tile config is required")
                return self


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
    overlay_vector_tile_server: AvailableVectorTileServerTypeAlias | None

    project_property_class = CompletenessProjectProperty
    project_task_group_property_class = CompletenessProjectTaskGroupProperty
    project_task_property_class = CompletenessProjectTaskProperty

    def __init__(self, project: Project):
        super().__init__(project)
        if typing.TYPE_CHECKING:
            assert project.project_type == ProjectTypeEnum.COMPLETENESS, f"{type(self)} is defined for COMPLETENESS"

        prop = self.project_type_specifics.overlay_tile_server_property
        self.overlay_vector_tile_server = (
            get_vector_tile_server(prop.vector.tile_server)
            if prop.type == OverlayLayerTypeEnum.VECTOR_TILE and prop.vector is not None
            else None
        )
        self.overlay_raster_tile_server = (
            get_tile_server(prop.raster.tile_server)
            if prop.type == OverlayLayerTypeEnum.RASTER_TILE and prop.raster is not None
            else None
        )

        # FIXME(tnagorra): Add this check
        # assert self.overlay_vector_tile_server is not None or self.overlay_raster_tile_server is not None,
        # f"Either vector or raster overlay should be defined"

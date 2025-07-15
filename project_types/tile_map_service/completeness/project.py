import typing

from django.db import models
from pydantic import BaseModel, field_validator, model_validator
from pyfirebase_mapswipe import models as firebase_models

from apps.project.models import Project, ProjectTypeEnum
from project_types.firebase import raster_tile_server_name_enum_to_firebase
from project_types.tile_map_service.base import project as base_project
from utils import fields as custom_fields
from utils.geo.raster_tile_server.models import RasterTileServerConfig
from utils.geo.vector_tile_server.models import VectorTileServerConfig


class OverlayLayerTypeEnum(models.TextChoices):
    VECTOR_TILE = "VECTOR_TILE", "Vector Tile"
    RASTER_TILE = "RASTER_TILE", "Raster Tile"


# FIXME(tnagorra): Add validations
class OverlayRasterTileServerConfig(BaseModel):
    tile_server: RasterTileServerConfig
    opacity: custom_fields.PydanticOpacity


# FIXME(tnagorra): Add validations
class OverlayVectorTileServerConfig(BaseModel):
    tile_server: VectorTileServerConfig

    fill_color: custom_fields.PydanticHexColor
    fill_opacity: custom_fields.PydanticOpacity

    line_color: custom_fields.PydanticHexColor
    line_opacity: custom_fields.PydanticOpacity
    line_width: custom_fields.PydanticPositiveFloat
    line_dasharray: list[custom_fields.PydanticPositiveInt]

    circle_color: custom_fields.PydanticHexColor
    circle_opacity: custom_fields.PydanticOpacity
    circle_radius: custom_fields.PydanticPositiveFloat


class OverlayTileServerConfig(BaseModel):
    type: OverlayLayerTypeEnum
    raster: OverlayRasterTileServerConfig | None = None
    vector: OverlayVectorTileServerConfig | None = None

    # TODO(tnagorra): Do we need to have a validation here for type?
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
    url_overlay_layer: custom_fields.PydanticUrl | None = None


class CompletenessProject(
    base_project.TileMapServiceBaseProject[
        CompletenessProjectProperty,
        CompletenessProjectTaskGroupProperty,
        CompletenessProjectTaskProperty,
    ],
):
    project_property_class = CompletenessProjectProperty
    project_task_group_property_class = CompletenessProjectTaskGroupProperty
    project_task_property_class = CompletenessProjectTaskProperty

    def __init__(self, project: Project):
        super().__init__(project)
        if typing.TYPE_CHECKING:
            assert project.project_type == ProjectTypeEnum.COMPLETENESS, f"{type(self)} is defined for COMPLETENESS"

    @typing.override
    def get_project_specifics_for_firebase(self):
        tsp = self.project_type_specifics.tile_server_property
        tsp_overlay = self.project_type_specifics.overlay_tile_server_property

        fb_tile_server = firebase_models.FbObjRasterTileServer(
            name=raster_tile_server_name_enum_to_firebase(tsp.name),
            credits=tsp.get_config()["credits"],
            url=tsp.get_config()["raw_url"],
            apiKey=tsp.get_config()["api_key"],
            # NOTE: wmtsLayerName is deprecated as singergise is not longer supported
            wmtsLayerName=firebase_models.UNDEFINED,
        )

        # NOTE: Setting background layer as fallback for overlay layer
        fb_overlay_tile_server = fb_tile_server
        # FIXME(tnagorra): Handle vector tiles in the future
        if tsp_overlay.type == OverlayLayerTypeEnum.RASTER_TILE and tsp_overlay.raster:
            fb_overlay_tile_server = firebase_models.FbObjRasterTileServer(
                name=raster_tile_server_name_enum_to_firebase(tsp_overlay.raster.tile_server.name),
                credits=tsp_overlay.raster.tile_server.get_config()["credits"],
                url=tsp_overlay.raster.tile_server.get_config()["raw_url"],
                apiKey=tsp_overlay.raster.tile_server.get_config()["api_key"],
                # NOTE: wmtsLayerName is deprecated as singergise is not longer supported
                wmtsLayerName=firebase_models.UNDEFINED,
            )

        return firebase_models.FbProjectCompareCreateOnlyInput(
            zoomLevel=self.project_type_specifics.zoom_level,
            tileServer=fb_tile_server,
            tileServerB=fb_overlay_tile_server,
        )

import typing

from django.db import models
from pydantic import BaseModel, field_validator, model_validator
from pyfirebase_mapswipe import models as firebase_models

from apps.project.models import Project, ProjectTypeEnum
from project_types.tile_map_service.base import project as base_project
from utils import fields as custom_fields
from utils.geo.raster_tile_server.models import RasterTileServerConfig
from utils.geo.vector_tile_server.models import VectorTileServerConfig

FALLBACK_RASTER_LAYER = (
    "https://raw.githubusercontent.com/mapswipe/mapswipe-assets/refs/heads/main/images/raster-layer-404-message.png"
)


class OverlayLayerTypeEnum(models.TextChoices):
    VECTOR_TILE = "VECTOR_TILE", "Vector Tile"
    RASTER_TILE = "RASTER_TILE", "Raster Tile"

    def to_firebase(self) -> firebase_models.FbEnumOverlayTileServerType:
        match self:
            case OverlayLayerTypeEnum.RASTER_TILE:
                return firebase_models.FbEnumOverlayTileServerType.RASTER
            case OverlayLayerTypeEnum.VECTOR_TILE:
                return firebase_models.FbEnumOverlayTileServerType.VECTOR


class OverlayRasterTileServerConfig(BaseModel):
    tile_server: RasterTileServerConfig
    opacity: custom_fields.PydanticOpacity


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
    # NOTE: We added URL as it's used directly when creating exports
    url_b: str


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
    def get_max_time_spend_percentile(self) -> float:
        return 1.4

    @typing.override
    def get_task_specifics_for_db(self, tile_x: int, tile_y: int) -> CompletenessProjectTaskProperty:
        url = self.project_type_specifics.tile_server_property.generate_url(
            tile_x,
            tile_y,
            self.project_type_specifics.zoom_level,
        )

        url_b: str | None = None
        if self.project_type_specifics.overlay_tile_server_property.raster:
            url_b = self.project_type_specifics.overlay_tile_server_property.raster.tile_server.generate_url(
                tile_x,
                tile_y,
                self.project_type_specifics.zoom_level,
            )
        elif self.project_type_specifics.overlay_tile_server_property.vector:
            url_b = self.project_type_specifics.overlay_tile_server_property.vector.tile_server.get_config()["url"]

        return self.project_task_property_class(
            tile_x=tile_x,
            tile_y=tile_y,
            url=url,
            url_b=url_b or url,
        )

    # FIREBASE

    @typing.override
    def get_project_specifics_for_firebase(self):
        tsp = self.project_type_specifics.tile_server_property
        tsp_overlay = self.project_type_specifics.overlay_tile_server_property

        fb_tile_server = firebase_models.FbObjRasterTileServer(
            name=tsp.name.to_firebase(),
            credits=tsp.get_config()["credits"],
            url=tsp.get_config()["raw_url"],
            apiKey=tsp.get_config()["api_key"],
            wmtsLayerName=None,
        )

        # NOTE: Setting background layer as fallback for overlay layer
        if tsp_overlay.type == OverlayLayerTypeEnum.RASTER_TILE and tsp_overlay.raster:
            fb_overlay_tile_server = firebase_models.FbObjRasterTileServer(
                name=tsp_overlay.raster.tile_server.name.to_firebase(),
                credits=tsp_overlay.raster.tile_server.get_config()["credits"],
                url=tsp_overlay.raster.tile_server.get_config()["raw_url"],
                apiKey=tsp_overlay.raster.tile_server.get_config()["api_key"],
                wmtsLayerName=None,
            )
        else:
            fb_overlay_tile_server = firebase_models.FbObjRasterTileServer(
                name=firebase_models.FbEnumRasterTileServerName.CUSTOM,
                credits="n/a",
                url=FALLBACK_RASTER_LAYER,
                apiKey="",
                wmtsLayerName=None,
            )

        return firebase_models.FbProjectCompletenessCreateOnlyInput(
            zoomLevel=self.project_type_specifics.zoom_level,
            tileServer=fb_tile_server,
            tileServerB=fb_overlay_tile_server,
            overlayTileServer=firebase_models.FbObjUnifiedOverlayTileServer(
                type=tsp_overlay.type.to_firebase(),
                vector=firebase_models.FbObjVectorTileServerOverlay(
                    tileServer=firebase_models.FbObjVectorTileServer(
                        name=tsp_overlay.vector.tile_server.name.to_firebase(),
                        sourceLayer=tsp_overlay.vector.tile_server.get_config()["source_layer"],
                        credits=tsp_overlay.vector.tile_server.get_config()["credits"],
                        url=tsp_overlay.vector.tile_server.get_config()["url"],
                        minZoom=tsp_overlay.vector.tile_server.get_config()["min_zoom"],
                        maxZoom=tsp_overlay.vector.tile_server.get_config()["max_zoom"],
                    ),
                    fillColor=tsp_overlay.vector.fill_color,
                    fillOpacity=tsp_overlay.vector.fill_opacity,
                    lineColor=tsp_overlay.vector.line_color,
                    lineOpacity=tsp_overlay.vector.line_opacity,
                    lineWidth=tsp_overlay.vector.line_width,
                    lineDasharray=tsp_overlay.vector.line_dasharray,
                    circleColor=tsp_overlay.vector.circle_color,
                    circleOpacity=tsp_overlay.vector.circle_opacity,
                    circleRadius=tsp_overlay.vector.circle_radius,
                )
                if tsp_overlay.vector
                else None,
                raster=firebase_models.FbObjRasterTileServerOverlay(
                    opacity=tsp_overlay.raster.opacity,
                    tileServer=firebase_models.FbObjRasterTileServer(
                        name=tsp_overlay.raster.tile_server.name.to_firebase(),
                        credits=tsp_overlay.raster.tile_server.get_config()["credits"],
                        url=tsp_overlay.raster.tile_server.get_config()["raw_url"],
                        apiKey=tsp_overlay.raster.tile_server.get_config()["api_key"],
                        wmtsLayerName=None,
                    ),
                )
                if tsp_overlay.raster
                else None,
            ),
        )

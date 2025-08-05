import typing

from pyfirebase_mapswipe import extended_models as firebase_ext_models
from pyfirebase_mapswipe import models as firebase_models

from apps.project.models import ProjectTypeEnum
from apps.tutorial.models import Tutorial, TutorialTask
from project_types.tile_map_service.base import tutorial as tile_map_service_tutorial

from .project import FALLBACK_RASTER_LAYER, CompletenessProjectProperty, OverlayLayerTypeEnum


class CompletenessTutorialTaskProperty(tile_map_service_tutorial.TileMapServiceTutorialTaskProperty): ...


class CompletenessTutorial(
    tile_map_service_tutorial.TileMapServiceBaseTutorial[
        CompletenessProjectProperty,
        CompletenessTutorialTaskProperty,
    ],
):
    project_property_class = CompletenessProjectProperty
    tutorial_task_property_class = CompletenessTutorialTaskProperty

    def __init__(self, tutorial: Tutorial):
        super().__init__(tutorial)

    @typing.override
    def get_task_specifics_for_firebase(self, task: TutorialTask, index: int):
        tsp = self.project_type_specifics.tile_server_property
        tsp_overlay = self.project_type_specifics.overlay_tile_server_property

        task_specifics = self.tutorial_task_property_class(
            **task.project_type_specifics,
        )

        resp = super().get_task_specifics_for_firebase(task, index)

        return firebase_ext_models.FbCompletenessTutorialTaskComplete(
            geometry=resp.geometry,
            groupId=resp.groupId,
            projectId=resp.projectId,
            referenceAnswer=resp.referenceAnswer,
            screen=resp.screen,
            taskId_real=resp.taskId_real,
            taskX=resp.taskX,
            taskY=resp.taskY,
            taskId=resp.taskId,
            url=tsp.generate_url(
                task_specifics.tile_x,
                task_specifics.tile_y,
                task_specifics.tile_z,
            ),
            urlB=tsp_overlay.raster.tile_server.generate_url(
                task_specifics.tile_x,
                task_specifics.tile_y,
                task_specifics.tile_z,
            )
            if tsp_overlay.type == OverlayLayerTypeEnum.RASTER_TILE and tsp_overlay.raster
            else FALLBACK_RASTER_LAYER,
        )

    @typing.override
    def get_tutorial_specifics_for_firebase(self):
        tsp = self.project_type_specifics.tile_server_property
        tsp_overlay = self.project_type_specifics.overlay_tile_server_property

        projectType = ProjectTypeEnum.COMPLETENESS.value
        assert projectType == 4, "Project Completeness should be 4"

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

        return firebase_models.FbCompletenessTutorial(
            zoomLevel=self.project_type_specifics.zoom_level,
            projectType=projectType,
            tileServer=firebase_models.FbObjRasterTileServer(
                name=tsp.name.to_firebase(),
                credits=tsp.get_config()["credits"],
                url=tsp.get_config()["raw_url"],
                apiKey=tsp.get_config()["api_key"],
                wmtsLayerName=None,
            ),
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

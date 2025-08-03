import json
import logging
import typing

from osgeo import ogr
from pyfirebase_mapswipe import extended_models as firebase_ext_models
from pyfirebase_mapswipe import models as firebase_models

from apps.project.models import ProjectTypeEnum
from apps.tutorial.models import Tutorial, TutorialTask
from project_types.base import tutorial as base_tutorial
from project_types.base.tutorial import BaseTutorialTaskProperty
from project_types.firebase import raster_tile_server_name_enum_to_firebase

from .project import ValidateProjectProperty

logger = logging.getLogger(__name__)


class ValidateTutorialTaskProperty(BaseTutorialTaskProperty):
    # FIXME(tnagorra): add positive integer
    identifier: int
    # FIXME(tnagorra): Use geometry from TutorialTask
    object_geometry: str


class ValidateTutorial(
    base_tutorial.BaseTutorial[
        ValidateProjectProperty,
        ValidateTutorialTaskProperty,
    ],
):
    project_property_class = ValidateProjectProperty
    tutorial_task_property_class = ValidateTutorialTaskProperty

    def __init__(self, tutorial: Tutorial):
        super().__init__(tutorial)

    @typing.override
    def get_task_tutorial_specifics_for_firebase(self, task: TutorialTask, index: int):
        task_specifics = self.tutorial_task_property_class(
            **task.project_type_specifics,
        )

        geojson = json.loads(task_specifics.object_geometry)
        geometry_ogr = ogr.CreateGeometryFromJson(task_specifics.object_geometry)
        geometry_wkt = geometry_ogr.ExportToWkt()

        return firebase_models.FbValidateTutorialTask(
            taskId=f"t{index}",
            geojson=geojson,
            properties=firebase_models.FbValidateTutorialTaskProperties(
                id=task_specifics.identifier,
                reference=task.reference,
                screen=task.scenario.scenario_page_number,
            ),
            geometry=geometry_wkt,
        )

    @typing.override
    def get_group_tutorial_specifics_for_firebase(self):
        return firebase_ext_models.FbEmptyModel()

    @typing.override
    def get_tutorial_specifics_for_firebase(self):
        tsp = self.project_type_specifics.tile_server_property
        custom_opts = self.project_type_specifics.custom_options

        projectType = ProjectTypeEnum.VALIDATE.value
        assert projectType == 2, "Project Validate should be 2"

        return firebase_models.FbValidateTutorial(
            # FIXME(tnagorra): This is the path to local storage.
            inputGeometries="",
            # FIXME(tnagorra): Check if this is always 18, app is calculating zoomLevel using geometry
            zoomLevel=18,
            projectType=projectType,
            tileServer=firebase_models.FbObjRasterTileServer(
                name=raster_tile_server_name_enum_to_firebase(tsp.name),
                credits=tsp.get_config()["credits"],
                url=tsp.get_config()["raw_url"],
                apiKey=tsp.get_config()["api_key"],
                wmtsLayerName=None,
            ),
            customOptions=[
                firebase_models.FbObjCustomOption(
                    title=opt.title,
                    description=opt.description,
                    value=opt.value,
                    icon=str(opt.icon.label),
                    iconColor=opt.icon_color,
                    subOptions=[
                        firebase_models.FbBaseObjCustomSubOption(
                            value=sub_opt.value,
                            description=sub_opt.description,
                        )
                        for sub_opt in opt.sub_options
                    ]
                    if opt.sub_options is not None
                    else None,
                )
                for opt in custom_opts
            ]
            if custom_opts is not None
            else None,
        )

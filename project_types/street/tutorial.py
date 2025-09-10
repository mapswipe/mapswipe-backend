import typing

from pyfirebase_mapswipe import models as firebase_models

from apps.project.models import ProjectTypeEnum
from apps.tutorial.models import Tutorial, TutorialTask
from project_types.base import tutorial as base_tutorial
from project_types.street.project import StreetProjectProperty
from utils.geo.transform import convert_json_str_to_wkt


class StreetTutorialTaskProperty(base_tutorial.BaseTutorialTaskProperty):
    # FIXME(tnagorra): Use geometry from TutorialTask
    object_geometry: str


# TODO(susilnem): This is not finalized
class StreetTutorial(
    base_tutorial.BaseTutorial[
        StreetProjectProperty,
        StreetTutorialTaskProperty,
    ],
):
    project_property_class = StreetProjectProperty
    tutorial_task_property_class = StreetTutorialTaskProperty

    def __init__(self, tutorial: Tutorial):
        super().__init__(tutorial)

    @typing.override
    def get_task_specifics_for_firebase(self, task: TutorialTask, index: int):
        task_specifics = self.tutorial_task_property_class(
            **task.project_type_specifics,
        )

        geometry_wkt = convert_json_str_to_wkt(task_specifics.object_geometry)

        return firebase_models.FbStreetTutorialTask(
            taskId=f"t{index}",
            geometry=geometry_wkt,
            screen=task.scenario.scenario_page_number,
            referenceAnswer=task.reference,
        )

    @typing.override
    def get_tutorial_specifics_for_firebase(self):
        custom_opts = self.project_type_specifics.custom_options

        projectType = ProjectTypeEnum.STREET.value
        assert projectType == 7, "Project Street should be 7"

        return firebase_models.FbStreetTutorial(
            zoomLevel=14,
            projectType=projectType,
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

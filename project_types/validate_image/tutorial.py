import logging
import typing

from pyfirebase_mapswipe import extended_models as firebase_ext_models
from pyfirebase_mapswipe import models as firebase_models

from apps.project.models import ProjectTypeEnum
from apps.tutorial.models import Tutorial, TutorialTask
from project_types.base import tutorial as base_tutorial
from project_types.base.tutorial import BaseTutorialTaskProperty
from utils.asset_types.models import ObjectImageAnnotation

from .project import ValidateImageProjectProperty

logger = logging.getLogger(__name__)


class ValidateImageTutorialTaskProperty(BaseTutorialTaskProperty):
    url: str
    file_name: str
    width: int | None = None
    height: int | None = None
    annotation: ObjectImageAnnotation | None = None


class ValidateImageTutorial(
    base_tutorial.BaseTutorial[
        ValidateImageProjectProperty,
        ValidateImageTutorialTaskProperty,
    ],
):
    project_property_class = ValidateImageProjectProperty
    tutorial_task_property_class = ValidateImageTutorialTaskProperty

    def __init__(self, tutorial: Tutorial):
        super().__init__(tutorial)

    @typing.override
    def get_task_specifics_for_firebase(self, task: TutorialTask, index: int):
        task_specifics = self.tutorial_task_property_class(
            **task.project_type_specifics,
        )

        return firebase_models.FbValidateImageTutorialTask(
            geometry="",
            groupId=self.get_tutorial_group_key(),
            projectId=self.tutorial.firebase_id,
            referenceAnswer=task.reference,
            screen=task.scenario.scenario_page_number,
            taskId=f"{index}",
            url=task_specifics.url,
            fileName=task_specifics.file_name,
            width=task_specifics.width,
            height=task_specifics.height,
            annotationId=task_specifics.annotation.id if task_specifics.annotation else None,
            bbox=list(task_specifics.annotation.bbox) if task_specifics.annotation else None,
            segmentation=task_specifics.annotation.segmentation if task_specifics.annotation else None,
        )

    @typing.override
    def get_group_specifics_for_firebase(self):
        return firebase_ext_models.FbEmptyModel()

    @typing.override
    def get_tutorial_specifics_for_firebase(self):
        custom_opts = self.project_type_specifics.custom_options

        projectType = ProjectTypeEnum.VALIDATE_IMAGE.value
        assert projectType == 10, "Project Validate Image should be 10"

        return firebase_models.FbValidateImageTutorial(
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

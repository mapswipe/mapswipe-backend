import typing

from pyfirebase_mapswipe import extended_models as firebase_ext_models
from pyfirebase_mapswipe import models as firebase_models

from apps.project.models import ProjectTypeEnum
from apps.tutorial.models import Tutorial, TutorialTask
from project_types.base import tutorial as base_tutorial
from project_types.street.project import StreetProjectProperty
from utils import fields as custom_fields


class StreetTutorialTaskProperty(base_tutorial.BaseTutorialTaskProperty):
    # FIXME: Why is this a long text instead of PydanticId
    mapillary_image_id: custom_fields.PydanticLongText
    # NOTE: geometry is not used but we are saving this for the records
    geometry: str


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
    def compress_tasks_on_firebase(self) -> bool:
        return True

    @typing.override
    def get_task_specifics_for_firebase(self, task: TutorialTask, index: int, screen: int):
        task_specifics = self.tutorial_task_property_class.model_validate(task.project_type_specifics)
        return firebase_models.FbStreetTutorialTask(
            projectId=self.tutorial.firebase_id,
            groupId=self.get_tutorial_group_key(),
            taskId=task_specifics.mapillary_image_id,
            geometry="",
            referenceAnswer=task.reference,
            screen=screen,
        )

    @typing.override
    def get_group_specifics_for_firebase(self):
        return firebase_ext_models.FbEmptyModel()

    @typing.override
    def get_tutorial_specifics_for_firebase(self):
        custom_opts = self.project_type_specifics.custom_options
        image_provider = self.project_type_specifics.image_provider

        projectType = ProjectTypeEnum.STREET.value
        assert projectType == 7, "Project Street should be 7"

        return firebase_models.FbStreetTutorial(
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
            imageProvider=firebase_models.FbObjImageProvider(
                name=image_provider.name,
                url=image_provider.url,
            ),
        )

import logging
import typing

from pyfirebase_mapswipe import models as firebase_models

from apps.project.models import Project
from project_types.base import project as base_project
from utils import fields as custom_fields
from utils.custom_options.models import CustomOption

logger = logging.getLogger(__name__)


class ValidateImageProjectProperty(base_project.BaseProjectProperty):
    annotations_file: custom_fields.PydanticId | None = None
    # FIXME(tnagorra): Do we use existing look_for or add a new field for question
    # base_question: custom_fields.PydanticLongText
    custom_options: list[CustomOption] | None = None


class ValidateImageProjectTaskGroupProperty(base_project.BaseProjectTaskGroupProperty): ...


class ValidateImageProjectTaskProperty(base_project.BaseProjectTaskProperty):
    # FIXME(tnagorra): Do we support custom question?
    question: custom_fields.PydanticLongText | None = None
    # TODO(tnagorra): Add image url
    # TODO(tnagorra): Add image annotations


class ValidateImageProject(
    base_project.BaseProject[
        ValidateImageProjectProperty,
        ValidateImageProjectTaskGroupProperty,
        ValidateImageProjectTaskProperty,
        typing.Any,
        typing.Any,
    ],
):
    project_property_class = ValidateImageProjectProperty
    project_task_group_property_class = ValidateImageProjectTaskGroupProperty
    project_task_property_class = ValidateImageProjectTaskProperty

    def __init__(self, project: Project):
        super().__init__(project)

    @typing.override
    def get_task_project_specifics_for_firebase(self, task):
        task_specifics = self.project_task_property_class(
            **task.project_type_specifics,
        )
        return firebase_models.FbMappingTaskValidateImageCreateOnlyInput(
            taskId=str(task.legacy_task_id),
            question=task_specifics.question or firebase_models.UNDEFINED,
        )

    @typing.override
    def get_group_project_specifics_for_firebase(self, group):
        return firebase_models.FbMappingGroupValidateImageCreateOnlyInput(
            groupId=str(group.legacy_group_id),
        )

    # TODO(tnagorra): Define validate
    # TODO(tnagorra): Define create_tasks
    # TODO(tnagorra): Define create_groups
    # TODO(tnagorra): Define post_create_groups
    # TODO(tnagorra): Define get_task_project_specifics_for_firebase
    # TODO(tnagorra): Define get_group_project_specifics_for_firebase

    @typing.override
    def get_project_specifics_for_firebase(self):
        custom_opts = self.project_type_specifics.custom_options
        return firebase_models.FbProjectValidateImageCreateOnlyInput(
            customOptions=[
                firebase_models.FbObjCustomOption(
                    title=opt.title,
                    description=opt.description,
                    value=opt.value,
                    icon=opt.icon.value,
                    iconColor=opt.icon_color,
                    subOptions=[
                        firebase_models.FbBaseObjCustomSubOption(
                            value=sub_opt.value,
                            description=sub_opt.description,
                        )
                        for sub_opt in opt.sub_options
                    ]
                    if opt.sub_options is not None
                    else firebase_models.UNDEFINED,
                )
                for opt in custom_opts
            ]
            if custom_opts is not None
            else firebase_models.UNDEFINED,
        )

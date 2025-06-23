import logging
import typing

from pydantic import BaseModel

from apps.project.models import Project
from project_types.base import project as base_project
from utils import fields as custom_fields

logger = logging.getLogger(__name__)


class ValidateImageProjectProperty(base_project.BaseProjectProperty):
    annotations_file: custom_fields.PydanticId
    base_question: custom_fields.PydanticLongText


class ValidateImageProjectTaskGroupProperty(base_project.BaseProjectTaskGroupProperty): ...


class ValidateImageProjectTaskProperty(base_project.BaseProjectTaskProperty):
    question: custom_fields.PydanticLongText


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
    def get_project_specifics_for_firebase(self, project_ref):
        class EmptyModel(BaseModel): ...

        return EmptyModel()

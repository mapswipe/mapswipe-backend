import logging
import typing

from pyfirebase_mapswipe import extended_models as firebase_ext_models

from apps.project.models import Project
from project_types.base import project as base_project
from utils import fields as custom_fields
from utils.custom_options.models import CustomOption

logger = logging.getLogger(__name__)


class ValidateImageProjectProperty(base_project.BaseProjectProperty):
    annotations_file: custom_fields.PydanticId | None = None
    # base_question: custom_fields.PydanticLongText
    custom_options: list[CustomOption] | None = None


class ValidateImageProjectTaskGroupProperty(base_project.BaseProjectTaskGroupProperty): ...


class ValidateImageProjectTaskProperty(base_project.BaseProjectTaskProperty):
    question: custom_fields.PydanticLongText | None = None


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
        return firebase_ext_models.FbEmptyModel()

    @typing.override
    def get_group_project_specifics_for_firebase(self, group):
        return firebase_ext_models.FbEmptyModel()

    @typing.override
    def get_project_specifics_for_firebase(self):
        return firebase_ext_models.FbEmptyModel()

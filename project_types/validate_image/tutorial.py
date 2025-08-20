import logging

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

import logging

from project_types.base.tutorial import BaseTutorialTaskProperty
from utils import fields as custom_fields

logger = logging.getLogger(__name__)


class ValidateImageTutorialTaskProperty(BaseTutorialTaskProperty):
    question: custom_fields.PydanticLongText

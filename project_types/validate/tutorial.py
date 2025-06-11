import logging
import typing

from pydantic import Field

from project_types.base.tutorial import BaseTutorialTaskProperty

logger = logging.getLogger(__name__)


class ValidateTutorialTaskProperty(BaseTutorialTaskProperty):
    object_geometry: typing.Annotated[str, Field(strict=True, pattern=r"^\d+$")] | None = None

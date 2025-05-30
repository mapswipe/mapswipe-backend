import logging
from abc import ABC

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class BaseTutorialTaskProperty(BaseModel, ABC): ...

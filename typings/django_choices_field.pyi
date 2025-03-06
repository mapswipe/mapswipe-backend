from typing import Type

from django.db import models

class IntegerChoicesField:
    def __init__(
        self,
        choices_enum: Type[models.IntegerChoices],
        **kwargs,
    ): ...

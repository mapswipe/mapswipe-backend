from django.db import models

class IntegerChoicesField:
    def __init__(
        self,
        choices_enum: type[models.IntegerChoices],
        **kwargs,
    ): ...

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class PercentageField(models.PositiveSmallIntegerField):
    def __init__(self, *args, **kwargs):
        kwargs["default"] = kwargs.get("default", 0)
        kwargs["validators"] = [
            MinValueValidator(0),
            MaxValueValidator(100),
            *kwargs.get("validators", []),
        ]
        super().__init__(*args, **kwargs)

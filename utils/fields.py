from django.core.exceptions import ValidationError
from django.utils.translation import gettext


def validate_percentage(value: float | int):
    if not (0 <= value <= 100):
        raise ValidationError(
            gettext("The value %(value)s is not a valid percentage. It should be between 0 and 100."),
            params={"value": value},
        )

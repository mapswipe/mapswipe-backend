import typing

from django.core.files.storage import storages
from django.db import models

from main.config import Config


class OverwritableFileField(models.FileField):
    def __new__init__(self, *args: typing.Any, **kwargs: typing.Any):
        kwargs.setdefault("storage", storages[Config.STORAGE_OVERWRITE_KEY])
        super().__init__(*args, **kwargs)

    @typing.override
    def get_prep_value(self, value):
        if value in ("", None):
            return None
        return super().get_prep_value(value)


# XXX: monkey patching to avoid removing OverwritableFileField.__init__ type annotations
OverwritableFileField.__init__ = OverwritableFileField.__new__init__

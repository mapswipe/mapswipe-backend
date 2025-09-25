import typing

from django.core.files.storage import storages
from django.db import models

from main.config import Config


class OverwritableFileField(models.FileField):
    def __new__init__(self, *args: typing.Any, **kwargs: typing.Any):
        kwargs.setdefault("storage", storages[Config.STORAGE_OVERWRITE_KEY])
        super().__init__(*args, **kwargs)

    @typing.override
    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        # This is also default_storage (with overwrite change)
        # FileField doesn't track default_storage in migrations
        # So we are also untracking the storage which is added by the FileField deconstruct
        if self.storage is storages[Config.STORAGE_OVERWRITE_KEY]:
            kwargs.pop("storage")
        return name, path, args, kwargs

    # TODO: Remove this... use blank=True and null=False for all FileFields
    # Use file='' instead of file__isnull=True in filters
    @typing.override
    def get_prep_value(self, value: typing.Any):
        if value in ("", None):
            return None
        return super().get_prep_value(value)


# XXX: monkey patching to avoid removing OverwritableFileField.__init__ type annotations
OverwritableFileField.__init__ = OverwritableFileField.__new__init__

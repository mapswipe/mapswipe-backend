import typing
import weakref

from django.conf import settings
from django.core.files.storage import Storage, storages
from django.core.signals import setting_changed
from django.db import models
from django.utils.functional import LazyObject, empty

from main.config import Config

# Keyed by id: LazyObject proxies __hash__ and __eq__ to the storage, which would resolve it
_lazy_storages: weakref.WeakValueDictionary[int, "LazyStorage"] = weakref.WeakValueDictionary()


class LazyStorage(LazyObject):
    """Resolve storages[key] on first use, and again after STORAGES changes (Eg: override_settings)."""

    def __init__(self, key: str):
        super().__init__()
        self.__dict__["storage_key"] = key
        _lazy_storages[id(self)] = self

    def _setup(self):
        self._wrapped = storages[self.__dict__["storage_key"]]  # type: ignore[reportUninitializedInstanceVariable]

    def reset(self):
        self._wrapped = empty


def _reset_lazy_storages(*, setting: str, **_: typing.Any):
    if setting != "STORAGES":
        return
    for lazy_storage in list(_lazy_storages.values()):
        lazy_storage.reset()


setting_changed.connect(_reset_lazy_storages)


class OverwritableFileField(models.FileField):
    """FileField using storages[storage_key] (resolved lazily) unless storage is passed."""

    storage_key: str = Config.STORAGE_OVERWRITE_KEY
    lazy_storage: Storage | None = None

    def __new__init__(self, *args: typing.Any, **kwargs: typing.Any):
        super().__init__(*args, **kwargs)
        if "storage" not in kwargs:
            # Assigned after FileField.__init__, whose isinstance check would resolve the storage
            self.lazy_storage = typing.cast("Storage", LazyStorage(self.storage_key))
            self.storage = self.lazy_storage

    def has_storage(self) -> bool:
        """Return False if the storage is selected by storage_key, which is not defined in STORAGES."""
        return self.lazy_storage is None or self.storage_key in settings.STORAGES

    @typing.override
    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        # The storage is selected by storage_key from STORAGES (like default_storage, which FileField doesn't track)
        if self.lazy_storage is not None and self.storage is self.lazy_storage:
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


class ShortTermFileField(OverwritableFileField):
    """OverwritableFileField using the short-term storage."""

    storage_key = Config.SHORT_TERM_STORAGE_KEY

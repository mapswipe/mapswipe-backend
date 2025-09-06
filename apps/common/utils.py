import typing

from django.core.files.storage import FileSystemStorage
from django.db.models.fields import files

from main.config import Config
from utils.common import is_file_empty


@typing.overload
def get_absolute_uri(file: None) -> None: ...


@typing.overload
def get_absolute_uri(file: files.FieldFile) -> str: ...


def get_absolute_uri(file: files.FieldFile | None) -> str | None:
    if is_file_empty(file):
        return None
    if isinstance(file.storage, FileSystemStorage):
        # FIXME(tnagorra): We should change the url method in storage
        return f"{Config.MEDIA_STORAGE_DOMAIN.geturl()}{file.url}"
    return file.url


def remove_object_keys(obj: typing.Any, keys_to_ignore: list[str] | set[str]):
    """Recursively remove keys from dicts if the key is in keys_to_ignore."""
    if isinstance(obj, dict):
        for key in list(obj.keys()):
            if key in keys_to_ignore:
                obj.pop(key)
            else:
                remove_object_keys(obj[key], keys_to_ignore)
    elif isinstance(obj, list):
        for item in obj:
            remove_object_keys(item, keys_to_ignore)
    return obj

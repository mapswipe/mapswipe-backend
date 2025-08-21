import typing

from django.core.files.storage import FileSystemStorage
from django.db.models.fields import files

from main.config import Config


@typing.overload
def get_absolute_uri(file: None) -> None: ...


@typing.overload
def get_absolute_uri(file: files.FieldFile) -> str: ...


def get_absolute_uri(file: files.FieldFile | None) -> str | None:
    if not file:
        return None
    if isinstance(file.storage, FileSystemStorage):
        # FIXME(tnagorra): We should change the url method in storage
        return f"{Config.MEDIA_STORAGE_DOMAIN.geturl()}{file.url}"
    return file.url

import base64
import csv
import gzip
import io
import json
import typing
from pathlib import Path

from django.core.files.storage import FileSystemStorage
from django.db.models.fields import files

from main.config import Config
from utils.common import is_file_empty

if typing.TYPE_CHECKING:
    from apps.project.models import ProjectAsset


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


# FIXME: move this to utils.common
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


def decode_tasks(encoded_task: str) -> list[dict[str, typing.Any]]:
    """Decode compressed task string back into list of dicts."""
    compressed_bytes = base64.b64decode(encoded_task)
    json_bytes = gzip.decompress(compressed_bytes)
    return json.loads(json_bytes.decode("utf-8"))


def compare_csv_files(
    project_asset: "ProjectAsset",
    expected_csv_path: Path,
    message: str,
    keys_to_ignore: list[str] | set[str] | None = None,
    is_gzip_file: bool = False,
) -> None:
    """Compare a CSV from a ProjectAsset with a plain CSV file.
    Supports gzipped CSV files when is_gzip_file=True.
    Raises AssertionError if differences are found.
    """
    if is_gzip_file:
        with (
            project_asset.file.open("rb") as file,
            gzip.GzipFile(fileobj=file, mode="rb") as gz,
            io.TextIOWrapper(gz, encoding="utf-8") as text_stream,
        ):
            actual_data = list(csv.DictReader(text_stream))
    else:
        with project_asset.file.open(mode="r") as file:
            actual_data = list(csv.DictReader(file))

    with expected_csv_path.open(mode="r", newline="", encoding="utf-8") as file:
        expected_data = list(csv.DictReader(file))

    if keys_to_ignore:
        actual_data = remove_object_keys(actual_data, keys_to_ignore)
        expected_data = remove_object_keys(expected_data, keys_to_ignore)

    assert actual_data == expected_data, message


def compare_geojson_files(
    project_asset: "ProjectAsset",
    expected_geojson_path: Path,
    message: str,
    keys_to_ignore: list[str] | set[str] | None = None,
    is_gzip_file: bool = False,
) -> None:
    """Compare a GeoJSON from a ProjectAsset with a plain GeoJSON file.
    Supports gzipped GeoJSON files when is_gzip_file=True.
    Raises AssertionError if differences are found.
    """
    if is_gzip_file:
        with (
            project_asset.file.open("rb") as file,
            gzip.GzipFile(fileobj=file, mode="rb") as gz,
            io.TextIOWrapper(gz, encoding="utf-8") as text_stream,
        ):
            actual_data = json.load(text_stream)
    else:
        with project_asset.file.open("r", encoding="utf-8") as file:
            actual_data = json.load(file)

    with expected_geojson_path.open("r", encoding="utf-8") as file:
        expected_data = json.load(file)

    if keys_to_ignore:
        actual_data = remove_object_keys(actual_data, keys_to_ignore)
        expected_data = remove_object_keys(expected_data, keys_to_ignore)

    assert actual_data == expected_data, message

import base64
import copy
import gzip
import io
import json
import re
import typing
from warnings import deprecated

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.translation import gettext
from geojson_pydantic import FeatureCollection
from ulid import ULID


def validate_imagery_url(url: str, *, support_quad_key: bool | None = True):
    """Check if imagery url contains xyz or quad key placeholders."""
    if all([substring in url for substring in ["{x}", "{y}", "{z}"]]) and not any(
        [substring in url for substring in ["{{x}}", "{{y}}", "{{z}}"]],
    ):
        return
    if all([substring in url for substring in ["{x}", "{-y}", "{z}"]]) and not any(
        [substring in url for substring in ["{{x}}", "{{-y}}", "{{z}}"]],
    ):
        return
    # NOTE: We are using quad_key instead of quad_key because client-side libraries directly supports quad_key
    if support_quad_key and ("{quad_key}" in url and "{{quad_key}}" not in url):
        return

    if support_quad_key:
        raise ValidationError(
            gettext("The imagery url '%s' must contain {x}, {y} (or {-y}) and {z} or the {quad_key} placeholders.") % url,
        )
    raise ValidationError(
        gettext("The imagery url '%s' must contain {x}, {y} (or {-y}) and {z} placeholders.") % url,
    )


def validate_ulid(val: str):
    # TODO: add suggestion for ULID value for local development (use settings.debug)
    if val == "":
        raise ValidationError(
            gettext("Empty string is not a valid ULID value"),
        )
    try:
        ULID.from_str(val)
    except (ValueError, TypeError) as e:
        raise ValidationError(
            gettext("'%s' is not a valid ULID value") % val,
        ) from e


def clean_up_none_keys(data: typing.Any):
    """
    Remove keys with none values (Also supports nested dict and list)
    Input:
     {"a": None, "b": "Hi"}
    Output:
     {"b": "Hi"}
    """

    if isinstance(data, list):
        return [clean_up_none_keys(x) for x in data]
    if isinstance(data, dict):
        _clone_data = copy.deepcopy(data)
        for key, value in data.items():
            if value is None:
                _clone_data.pop(key)
            else:
                _clone_data[key] = clean_up_none_keys(value)
        return _clone_data
    return data


def format_object_keys(
    obj: dict[typing.Any, typing.Any] | list[typing.Any] | typing.Any,
    formatter: typing.Callable[[str], str],
):
    if isinstance(obj, dict):
        new_obj = {}
        for key, value in obj.items():
            new_key = formatter(key) if isinstance(key, str) else key
            new_obj[new_key] = format_object_keys(value, formatter)
        return new_obj
    if isinstance(obj, list):
        return [format_object_keys(item, formatter) for item in obj]
    return obj


# Adapted from this response in Stackoverflow
# http://stackoverflow.com/a/19053800/1072990
def to_camel_case(snake_str: str):
    components = snake_str.split("_")
    # We capitalize the first letter of each component except the first one
    # with the 'capitalize' method and join them together.
    return components[0] + "".join(x.capitalize() if x else "_" for x in components[1:])


def to_snake_case(name: str):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def create_json_dump(item: dict[typing.Any, typing.Any]) -> bytes:
    return json.dumps(
        item,
        cls=DjangoJSONEncoder,
    ).encode("utf-8")


def parse_b64gzjson_to_dict(text: str) -> dict[str, typing.Any]:
    """
    Parse output of `gzip -cn file.json | base64 -w 0` to dict
    """
    gzipped_bytes = base64.b64decode(text)
    with gzip.GzipFile(fileobj=io.BytesIO(gzipped_bytes)) as f:
        json_bytes = f.read()
        return json.loads(json_bytes.decode("utf-8"))


@deprecated("We can directly use geojson_pydantic with more specific geometry")
def validate_geojson_file(file: ContentFile) -> None:
    """
    Validates if the given file contains a valid GeoJSON FeatureCollection.

    Args:
        file: File object

    Raises:
        ValidationError: If the file is not a valid JSON or does not conform to GeoJSON standards.
        ValueError: If the GeoJSON doesn't meet expected structure.
    """

    try:
        geojson_data = json.load(file)
    except json.JSONDecodeError as e:
        raise ValidationError("Invalid JSON format in the file.") from e

    feature_collection = FeatureCollection(**geojson_data)

    if not feature_collection.features:
        raise ValidationError("GeoJSON 'features' list cannot be empty.")


def gzip_str(string_: str) -> bytes:
    """
    Produce a complete gzip-compatible binary string.
    """
    out = io.BytesIO()
    # NOTE : mtime=0 (keeps timestamp constant which result same zip output each time)
    with gzip.GzipFile(fileobj=out, mode="w", mtime=0) as f:
        f.write(string_.encode())
    return out.getvalue()


def compress_tasks(tasks_list: list[dict[str, typing.Any]]) -> str:
    """
    Compress tasks for validate project type using gzip.
    """
    # FIXME(tnagorra): Removed replace(" ", "").replace("\n", "")
    json_string_tasks = json.dumps(tasks_list)
    compressed_tasks = gzip_str(json_string_tasks)
    # we need to decode back, but only when using Python 3.6
    # when using Python 3.7 it just works
    # Unfortunately the docker image uses Python 3.6
    return base64.b64encode(compressed_tasks).decode("ascii")

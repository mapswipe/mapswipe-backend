import datetime
import json
import logging
from typing import Any
from xml.etree import ElementTree as ET

import pyarrow as pa  # type: ignore[reportMissingTypeStubs]
import pyarrow.parquet as pq  # type: ignore[reportMissingTypeStubs]
import requests
from django.contrib.gis.geos import GEOSGeometry
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from main.config import Config
from main.logging import log_extra_response
from utils.fields import PydanticLongText

OHSOME_STATS_COUNT_PATH = "stats/features/count.json"
OHSOME_EXTRACTION_FEATURES_PATH = "extraction/features.parquet"

# NOTE: The API requires an explicit time. "latest" is the current snapshot.
OHSOME_SNAPSHOT_TIME = "latest"

OHSOME_REQUIRED_COLUMNS = (
    "osm_type",
    "osm_id",
    "version",
    "changeset_id",
    "edit_timestamp",
    "user_id",
    "user_name",
    "geom",
    "geom_type",
)

logger = logging.getLogger(__name__)


class ValidateApiCallError(Exception):
    pass


def remove_troublesome_chars(string: str | None):
    """Remove chars that cause trouble when pushed into postgres."""
    if type(string) is not str:
        return string
    troublesome_chars = {'"': "", "'": "", "\n": " "}
    for k, v in troublesome_chars.items():
        string = string.replace(k, v)
    return string


def retry_get(url: str, retries: int | None = 3, timeout: int | None = 10, to_osmcha: bool = False):
    """Retry a query for a variable amount of tries."""
    retry = Retry(total=retries)
    with requests.Session() as session:
        session.mount("https://", HTTPAdapter(max_retries=retry))
        if to_osmcha:
            headers = {"Authorization": f"Token {Config.OSMCHA_API_KEY}"}
            return session.get(url, timeout=timeout, headers=headers)
        return session.get(url, timeout=timeout, headers=Config.DEFAULT_HEADERS)


# FIXME(rup): Not used anywhere
def geojsonToFeatureCollection(geojson: dict) -> dict:  # type: ignore[reportMissingTypeArgument]
    """Take a GeoJson and wrap it in a FeatureCollection."""
    if geojson["type"] != "FeatureCollection":
        return {
            "type": "FeatureCollection",
            "features": [{"type": "feature", "geometry": geojson}],
        }
    return geojson


def chunks[T](arr: list[T], n_objects: int) -> list[list[T]]:
    """Return a list of list with n_objects in each sublist."""
    return [arr[i * n_objects : (i + 1) * n_objects] for i in range((len(arr) + n_objects - 1) // n_objects)]


def query_osmcha(changeset_ids: list, changeset_results: dict[int, Any]):  # type: ignore[reportMissingTypeArgument]
    """Get data from changesetId."""
    id_string = ",".join(map(str, changeset_ids))

    url = Config.OSMCHA_API_LINK + f"changesets/?ids={id_string}"
    response = retry_get(url, to_osmcha=True)
    if response.status_code != 200:
        logger.warning(
            "osmcha request failed",
            extra=log_extra_response(response=response),
        )
        raise ValidateApiCallError
    response = response.json()
    for feature in response["features"]:
        changeset_results[int(feature["id"])] = {
            "username": remove_troublesome_chars(feature["properties"]["user"]),
            "userid": feature["properties"]["uid"],
            "comment": remove_troublesome_chars(feature["properties"]["comment"]),
            "editor": remove_troublesome_chars(feature["properties"]["editor"]),
        }

    return changeset_results


def query_osm(changeset_ids: list, changeset_results: dict):  # type: ignore[reportMissingTypeArgument]
    """Get data from changesetId."""
    id_string = ",".join(map(str, changeset_ids))

    url = Config.OSM_API_LINK + f"changesets?changesets={id_string}"
    response = retry_get(url)
    if response.status_code != 200:
        logger.warning(
            "osm request failed",
            extra=log_extra_response(response=response),
        )
        raise ValidateApiCallError
    tree = ET.fromstring(response.content)  # noqa: S314

    for changeset in tree.iter("changeset"):
        changeset_id = changeset.attrib["id"]
        username = remove_troublesome_chars(changeset.attrib["user"])
        userid = changeset.attrib["uid"]
        comment = created_by = None
        for tag in changeset.iter("tag"):
            if tag.attrib["k"] == "comment":
                comment = tag.attrib["v"]
            if tag.attrib["k"] == "created_by":
                created_by = tag.attrib["v"]

        changeset_results[int(changeset_id)] = {
            "username": remove_troublesome_chars(username),
            "userid": userid,
            "comment": remove_troublesome_chars(comment),
            "editor": remove_troublesome_chars(created_by),
        }
    return changeset_results


def add_changeset_info(feature_collection: dict[str, Any]) -> dict[str, Any]:
    """Add the changeset comment and editor to each feature.

    osmCHA does not know every changeset, so the OSM API covers the rest.
    Only the comment and editor are fetched; the extraction already carries the user.
    """
    logger.info("starting changeset enrichment")
    batch_size = 100

    changeset_results: dict[int, Any] = {
        int(feature["properties"]["changesetId"]): None for feature in feature_collection["features"]
    }

    chunk_list = chunks(list(changeset_results.keys()), batch_size)
    logger.info(
        "%s changesets will be queried in %s batches from osmCHA",
        len(changeset_results),
        len(chunk_list),
    )
    for i, subset in enumerate(chunk_list):
        changeset_results = query_osmcha(subset, changeset_results)
        logger.info("finished query %s/%s", i + 1, len(chunk_list))

    missing_ids = [i for i, v in changeset_results.items() if v is None]
    if missing_ids:
        chunk_list = chunks(missing_ids, batch_size)
        logger.info(
            "%s changesets where missing from osmCHA and are now queried via osmAPI in %s batches",
            len(missing_ids),
            len(chunk_list),
        )
        for i, subset in enumerate(chunk_list):
            changeset_results = query_osm(subset, changeset_results)
            logger.info("finished query %s/%s", i + 1, len(chunk_list))

    unresolved = 0
    for feature in feature_collection["features"]:
        changeset = changeset_results.get(int(feature["properties"]["changesetId"]))
        if changeset is None:
            # NOTE: Neither osmCHA nor the OSM API knew this changeset
            unresolved += 1
            feature["properties"]["comment"] = None
            feature["properties"]["editor"] = None
            continue
        feature["properties"]["comment"] = changeset["comment"]
        feature["properties"]["editor"] = changeset["editor"]

    logger.info("finished changeset enrichment")
    if unresolved:
        logger.warning("%s features have no changeset info from osmCHA or osmAPI", unresolved)

    return feature_collection


def _format_ohsome_timestamp(value: datetime.datetime | None) -> str | None:
    """Format a timestamp for the task CSV export."""
    if value is None:
        return None
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def _ohsome_post(path: str, payload: dict[str, Any]) -> requests.Response:
    """POST a JSON body to the ohsome API and return the raw response."""
    url = Config.OHSOME_API_LINK + path
    headers = {
        **Config.DEFAULT_HEADERS,
        # NOTE: The API accepts the key bare or with a "Bearer " prefix
        "Authorization": Config.OHSOME_API_KEY,
    }

    logger.info("Target: %s", url)
    logger.info("Filter: %s", payload.get("filter"))

    # FIXME(tnagorra): Need to check what the timeout should be
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=100)
    except requests.exceptions.Timeout as e:
        logger.warning("ohsome request timed out: %s", path)
        raise ValidateApiCallError("OHSOME request timed out.") from e

    if response.status_code != 200:
        logger.warning(
            "ohsome request failed: check for errors in filter or geometries",
            extra=log_extra_response(response=response),
        )
        raise ValidateApiCallError
    logger.info("Query successful.")

    return response


def get_object_count_from_ohsome(aoi: dict[str, Any], ohsome_filter: PydanticLongText) -> int | None:
    """Count objects matching the filter within the area of interest.

    `aoi` takes one Polygon or MultiPolygon. A Feature or FeatureCollection is rejected.
    """
    response = _ohsome_post(
        OHSOME_STATS_COUNT_PATH,
        {
            "aoi": aoi,
            "filter": ohsome_filter,
            "time": OHSOME_SNAPSHOT_TIME,
        },
    )

    # NOTE: Results are columnar: {"result": {"timestamp": [...], "value": [...]}}
    result = response.json().get("result") or {}
    values = result.get("value") or []
    if not values:
        return None

    return int(values[0])


def parquet_to_feature_collection(content: bytes) -> dict[str, Any]:
    """Convert an ohsome parquet extraction into a GeoJSON FeatureCollection.

    The property names become columns of the public task CSV export, so renaming one
    changes that export.
    """
    table = pq.read_table(pa.BufferReader(content))

    missing_columns = [column for column in OHSOME_REQUIRED_COLUMNS if column not in table.column_names]
    if missing_columns:
        logger.warning("ohsome parquet is missing expected columns: %s", missing_columns)
        raise ValidateApiCallError(f"OHSOME response is missing expected columns: {missing_columns}")

    features: list[dict[str, Any]] = [
        {
            "type": "Feature",
            # NOTE: GEOSGeometry reads WKB from a memoryview. Plain bytes are read as text.
            "geometry": json.loads(GEOSGeometry(memoryview(row["geom"]), srid=4326).geojson),
            # NOTE: These names become task CSV export columns. The order here is lost:
            # the properties are stored as jsonb, which sorts keys by length then bytes.
            # comment and editor stay None here; add_changeset_info fills them in.
            "properties": {
                "changesetId": row["changeset_id"],
                "lastEdit": _format_ohsome_timestamp(row["edit_timestamp"]),
                # NOTE: The export column expects a single "way/123" string.
                "osmId": f"{row['osm_type']}/{row['osm_id']}",
                "version": row["version"],
                "username": remove_troublesome_chars(row["user_name"]),
                "comment": None,
                "editor": None,
                "userid": row["user_id"],
            },
        }
        for row in table.select(OHSOME_REQUIRED_COLUMNS).to_pylist()
    ]

    return {"type": "FeatureCollection", "features": features}


def get_objects_from_ohsome(aoi: dict[str, Any], ohsome_filter: PydanticLongText) -> dict[str, Any]:
    """Extract objects matching the filter within the area of interest, with changeset info.

    `aoi` has the same single-geometry restriction as `get_object_count_from_ohsome`.
    """
    response = _ohsome_post(
        OHSOME_EXTRACTION_FEATURES_PATH,
        {
            "aoi": aoi,
            "filter": ohsome_filter,
            "time": OHSOME_SNAPSHOT_TIME,
            "clip": False,
        },
    )

    return add_changeset_info(parquet_to_feature_collection(response.content))

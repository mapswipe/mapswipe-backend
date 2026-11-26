import datetime
import json
import logging
from typing import Any

import pyarrow as pa  # type: ignore[reportMissingTypeStubs]
import pyarrow.parquet as pq  # type: ignore[reportMissingTypeStubs]
import requests
from django.contrib.gis.geos import GEOSGeometry

from main.config import Config
from main.logging import log_extra_response
from utils.fields import PydanticLongText

OHSOME_STATS_COUNT_PATH = "stats/features/count.json"
OHSOME_EXTRACTION_FEATURES_PATH = "extraction/features.parquet"
OHSOME_EXTRACTION_CONTRIBUTIONS_PATH = "extraction/contributions.parquet"

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

OHSOME_CONTRIBUTIONS_REQUIRED_COLUMNS = (
    "osm_type",
    "osm_id",
    "changeset_id",
    "changeset_tags",
)

# NOTE: Changesets per contributions request. The filter grows with the page, so keep it
# well below the 413 limit.
OHSOME_CHANGESET_PAGE_SIZE = 10_000

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
    # NOTE: A contributions filter lists up to OHSOME_CHANGESET_PAGE_SIZE changesets
    logger.info("Filter: %.500s", payload.get("filter"))

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
            # comment and editor stay None here; add_changeset_tags fills them in.
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


type ChangesetTagsKey = tuple[str, int]


def parquet_to_changeset_tags(content: bytes) -> dict[ChangesetTagsKey, dict[str, str | None]]:
    """Read the changeset tags of an ohsome contributions extraction.

    Keyed by osmId ("way/123") and changesetId, the properties a feature of the features
    extraction carries. Every contribution of a changeset has the same changeset tags, so
    which of an object's contributions in a changeset is kept does not matter.
    """
    table = pq.read_table(pa.BufferReader(content))

    missing_columns = [column for column in OHSOME_CONTRIBUTIONS_REQUIRED_COLUMNS if column not in table.column_names]
    if missing_columns:
        logger.warning("ohsome contributions parquet is missing expected columns: %s", missing_columns)
        raise ValidateApiCallError(f"OHSOME response is missing expected columns: {missing_columns}")

    return {
        (f"{row['osm_type']}/{row['osm_id']}", row["changeset_id"]): (
            # NOTE: pyarrow reads a map column as a list of (key, value) pairs
            dict(row["changeset_tags"] or [])
        )
        for row in table.select(OHSOME_CONTRIBUTIONS_REQUIRED_COLUMNS).to_pylist()
    }


def get_changeset_pages(feature_collection: dict[str, Any]) -> list[tuple[str, list[int]]]:
    """Split the changesets of the features into pages for the contributions extraction.

    Each page is a start time and up to OHSOME_CHANGESET_PAGE_SIZE changeset ids. The
    changesets are ordered by their oldest edit, so each page starts at the oldest
    edit_timestamp in it and requests no older history than it needs.
    """
    # NOTE: An empty string sorts before every timestamp and is requested as "earliest"
    oldest_edit: dict[int, str] = {}
    for feature in feature_collection["features"]:
        changeset_id = int(feature["properties"]["changesetId"])
        # NOTE: lastEdit is "%Y-%m-%dT%H:%M:%SZ", so it sorts as text, and is truncated to the
        # second, so it is never later than the edit it comes from
        last_edit = feature["properties"]["lastEdit"] or ""
        oldest_edit[changeset_id] = min(oldest_edit.get(changeset_id, last_edit), last_edit)

    changeset_ids = sorted(oldest_edit, key=lambda changeset_id: (oldest_edit[changeset_id], changeset_id))
    return [
        (oldest_edit[paged_changeset_ids[0]] or "earliest", paged_changeset_ids)
        for paged_changeset_ids in chunks(changeset_ids, OHSOME_CHANGESET_PAGE_SIZE)
    ]


def add_changeset_tags(
    aoi: dict[str, Any],
    ohsome_filter: PydanticLongText,
    feature_collection: dict[str, Any],
) -> dict[str, Any]:
    """Fill the comment and editor of each feature from the tags of its changeset.

    The features extraction has no changeset tags. The contributions extraction has them, so
    the contributions with the same aoi and filter, limited to the changesets of the features,
    are joined to the features on osmId and changesetId.
    """
    pages = get_changeset_pages(feature_collection)
    logger.info(
        "%s changesets will be queried from ohsome in %s pages",
        sum(len(changeset_ids) for _, changeset_ids in pages),
        len(pages),
    )

    changeset_tags: dict[ChangesetTagsKey, dict[str, str | None]] = {}
    for i, (start_datetime, changeset_ids) in enumerate(pages):
        response = _ohsome_post(
            OHSOME_EXTRACTION_CONTRIBUTIONS_PATH,
            {
                "aoi": aoi,
                "filter": f"({ohsome_filter}) and changeset:({','.join(map(str, changeset_ids))})",
                "time": {"start": start_datetime, "end": "latest"},
            },
        )
        changeset_tags.update(parquet_to_changeset_tags(response.content))
        logger.info("finished page %s/%s", i + 1, len(pages))

    unresolved = 0
    for feature in feature_collection["features"]:
        properties = feature["properties"]
        tags = changeset_tags.get((properties["osmId"], int(properties["changesetId"])))
        if tags is None:
            # NOTE: comment and editor stay None
            unresolved += 1
            continue
        properties["comment"] = remove_troublesome_chars(tags.get("comment"))
        properties["editor"] = remove_troublesome_chars(tags.get("created_by"))

    if unresolved:
        logger.warning("%s features have no contribution in the ohsome contributions extraction", unresolved)

    return feature_collection


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

    return add_changeset_tags(aoi, ohsome_filter, parquet_to_feature_collection(response.content))

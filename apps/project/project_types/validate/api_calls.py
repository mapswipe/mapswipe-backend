import logging
from typing import Any
from xml.etree import ElementTree as ET

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from main.config import Config

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


def retry_get(url: str, retries: int | None = 3, timeout: int | None = 4, to_osmcha: bool = False):
    """Retry a query for a variable amount of tries."""
    retry = Retry(total=retries)
    with requests.Session() as session:
        session.mount("https://", HTTPAdapter(max_retries=retry))
        if to_osmcha:
            headers = {"Authorization": f"Token {Config.OSMCHA_API_KEY}"}
            return session.get(url, timeout=timeout, headers=headers)
        return session.get(url, timeout=timeout)


def geojsonToFeatureCollection(geojson: dict) -> dict:
    """Take a GeoJson and wrap it in a FeatureCollection."""
    if geojson["type"] != "FeatureCollection":
        return {
            "type": "FeatureCollection",
            "features": [{"type": "feature", "geometry": geojson}],
        }
    return geojson


def chunks(arr: list, n_objects: int):
    """Return a list of list with n_objects in each sublist."""
    return [arr[i * n_objects : (i + 1) * n_objects] for i in range((len(arr) + n_objects - 1) // n_objects)]


def query_osmcha(changeset_ids: list, changeset_results: dict):
    """Get data from changesetId."""
    id_string = ",".join(map(str, changeset_ids))

    url = Config.OSMCHA_API_LINK + f"changesets/?ids={id_string}"
    response = retry_get(url, to_osmcha=True)
    if response.status_code != 200:
        err = f"osmcha request failed: {response.status_code}"
        logger.warning(f"{err}")  # noqa E501
        logger.warning(response.json())
        raise ValidateApiCallError(err)
    response = response.json()
    for feature in response["features"]:
        changeset_results[int(feature["id"])] = {
            "username": remove_troublesome_chars(feature["properties"]["user"]),
            "userid": feature["properties"]["uid"],
            "comment": remove_troublesome_chars(feature["properties"]["comment"]),
            "editor": remove_troublesome_chars(feature["properties"]["editor"]),
        }

    return changeset_results


def query_osm(changeset_ids: list, changeset_results: dict):
    """Get data from changesetId."""
    id_string = ",".join(map(str, changeset_ids))

    url = Config.OSM_API_LINK + f"changesets?changesets={id_string}"
    response = retry_get(url)
    if response.status_code != 200:
        err = f"osm request failed: {response.status_code}"
        logger.warning(f"{err}")  # noqa E501
        logger.warning(response.json())
        raise ValidateApiCallError(err)
    tree = ET.fromstring(response.content)

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


def remove_noise_and_add_user_info(json: dict[str, Any]) -> dict[str, Any]:
    """Delete unwanted information from properties."""
    logger.info("starting filtering and adding extra info")
    batch_size = 100

    # remove noise
    changeset_results = {}

    missing_rows = {
        "@changesetId": 0,
        "@lastEdit": 0,
        "@osmId": 0,
        "@version": 0,
    }

    for feature in json["features"]:
        new_properties = {}
        for attribute in missing_rows:
            try:
                new_properties[attribute.replace("@", "")] = feature["properties"][attribute]
            except KeyError:
                missing_rows[attribute] += 1
        changeset_results[new_properties["changesetId"]] = None
        feature["properties"] = new_properties

    # add info
    len_osm = len(changeset_results.keys())
    batches = int(len(changeset_results.keys()) / batch_size) + 1
    logger.info(
        f"""{len_osm} changesets will be queried in roughly {batches} batches from osmCHA"""  # noqa E501
    )

    chunk_list = chunks(list(changeset_results.keys()), batch_size)
    for i, subset in enumerate(chunk_list):
        changeset_results = query_osmcha(subset, changeset_results)
        progress = round(100 * ((i + 1) / len(chunk_list)), 1)
        logger.info(f"finished query {i + 1}/{len(chunk_list)}, {progress}")  # noqa E501

    missing_ids = [i for i, v in changeset_results.items() if v is None]
    chunk_list = chunks(missing_ids, batch_size)
    batches = int(len(missing_ids) / batch_size) + 1
    logger.info(
        f"""{len(missing_ids)} changesets where missing from osmCHA and are now queried via osmAPI in {batches} batches"""  # noqa E501
    )
    for i, subset in enumerate(chunk_list):
        changeset_results = query_osm(subset, changeset_results)
        progress = round(100 * ((i + 1) / len(chunk_list)), 1)
        logger.info(f"finished query {i + 1}/{len(chunk_list)}, {progress}")  # noqa E501

    for feature in json["features"]:
        changeset = changeset_results[int(feature["properties"]["changesetId"])]
        for attribute_name in ["username", "comment", "editor", "userid"]:
            if attribute_name == "userid":
                feature["properties"][attribute_name] = int(changeset[attribute_name])
            else:
                feature["properties"][attribute_name] = changeset[attribute_name]

    logger.info("finished filtering and adding extra info")
    if any(x > 0 for x in missing_rows.values()):
        logger.warning(f"features missing values:\n{missing_rows}")  # noqa E501

    return json


def ohsome(request: dict[str, Any], area: str, properties: str | None = None) -> dict[str, Any]:
    """Request data from Ohsome API."""
    url = Config.OHSOME_API_LINK + request["endpoint"]
    data = {"bpolys": area, "filter": request["filter"]}
    if properties:
        data["properties"] = properties
    logger.info("Target: " + url)  # noqa E501
    logger.info("Filter: " + request["filter"])  # noqa E501
    response = requests.post(url, data=data)
    if response.status_code != 200:
        err = f"ohsome request failed: {response.status_code}"
        logger.warning(
            f"{err} - check for errors in filter or geometries - {request['filter']}",  # noqa E501
        )
        logger.warning(response.json())
        raise ValidateApiCallError(err)
    logger.info("Query successful.")

    response = response.json()

    if properties:
        return remove_noise_and_add_user_info(response)

    return response

import contextlib
import gzip
import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from main.config import Config

logger = logging.getLogger(__name__)


def add_metadata_to_geojson(filename: Path):
    """
    Add a metadata attribute to the geojson file about intended data usage.
    """

    with Path.open(filename, mode="r") as f:
        geojson_data = json.load(f)

    if len(geojson_data["features"]) < 1:
        logger.info("there are no features for this file: %s", filename)
        return

    geojson_data["metadata"] = {
        "usage": "This data can only be used for editing in OpenStreetMap.",
    }

    with Path.open(filename, mode="w") as f:
        json.dump(geojson_data, f)

    logger.info("added metadata to %s.", filename)


def cast_datatypes_for_geojson(filename: Path):
    """
    Go through geojson file and try to cast all values as float, except project_id
    remove redundant geometry property
    """

    with Path.open(filename) as f:
        geojson_data = json.load(f)

    if len(geojson_data["features"]) < 1:
        logger.info("there are no features for this file: %s", filename)
        return

    properties = list(geojson_data["features"][0]["properties"].keys())
    for i in range(len(geojson_data["features"])):
        for property_ in properties:
            if property_ in [
                "project_id",
                "name",
                "project_details",
                "task_id",
                "group_id",
            ]:
                # don't try to cast project_id
                continue

            if property_ == "geom":
                # remove redundant geometry property
                del geojson_data["features"][i]["properties"][property_]
                continue

            if not geojson_data["features"][i]["properties"][property_]:
                del geojson_data["features"][i]["properties"][property_]
                continue

            with contextlib.suppress(ValueError, TypeError):
                geojson_data["features"][i]["properties"][property_] = float(
                    geojson_data["features"][i]["properties"][property_],
                )

    with Path.open(filename, "w") as f:
        json.dump(geojson_data, f)

    logger.info("converted datatypes for %s", filename)


def gzipped_csv_to_gzipped_geojson(
    *,
    gzip_csv_source_filename: Path,
    destination_filename: Path,
    geometry_field: str = "geom",
    add_metadata: bool = False,
):
    """Convert gzipped csv file to gzipped GeoJSON.

    First the gzipped files are unzipped and stored in temporary csv and geojson files.
    Then the unzipped csv file is converted into a geojson file with ogr2ogr.
    Last, the generated geojson file is again compressed using gzip.
    """
    with (
        tempfile.NamedTemporaryFile(suffix=".csv", dir=Config.TEMP_DIR) as tmp_extracted_csv_file,
    ):
        # uncompress content of zipped csv file and save to csv file
        with gzip.open(gzip_csv_source_filename, "rb") as f_in:
            shutil.copyfileobj(f_in, tmp_extracted_csv_file)
        tmp_extracted_csv_file.flush()

        tmp_geojson_filename = Path(tmp_extracted_csv_file.name.replace(".csv", ".geojson"))

        # use ogr2ogr to transform csv file into geojson file
        # TODO: remove geom column from normal attributes in sql query
        subprocess.run(  # noqa: S603
            [
                "/usr/bin/ogr2ogr",
                "-f",
                "GeoJSON",
                tmp_geojson_filename,
                tmp_extracted_csv_file.name,
                "-sql",
                f'SELECT *, CAST({geometry_field} as geometry) FROM "{Path(tmp_extracted_csv_file.name).stem}"',
            ],
            check=True,
        )

        if add_metadata:
            # TODO: Can we move this to ogr2ogr?
            add_metadata_to_geojson(tmp_geojson_filename)

        cast_datatypes_for_geojson(tmp_geojson_filename)

        # compress geojson file with gzip
        with (
            Path.open(tmp_geojson_filename, "rb") as f_in,
            gzip.open(destination_filename, "wb") as f_out,
        ):
            shutil.copyfileobj(f_in, f_out)

        # Delete the temporary file
        tmp_geojson_filename.unlink()

        logger.info("converted %s to %s with ogr2ogr.", gzip_csv_source_filename, destination_filename)

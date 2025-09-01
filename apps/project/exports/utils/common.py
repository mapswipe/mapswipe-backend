import gzip
import json
import logging
import tempfile
import typing
from pathlib import Path

import pandas as pd
from django.db import connection
from pandas.api.types import is_numeric_dtype
from psycopg2 import sql

from main.config import Config

logger = logging.getLogger(__name__)


def load_df_from_csv(filename: Path) -> pd.DataFrame:
    """Load a csv file into a pandas dataframe.
    Make sure that project_id, group_id and task_id are read as strings.
    """
    df = pd.read_csv(
        filename,
        dtype={
            "project_id": str,
            "group_id": str,
            "task_id": str,
        },
        compression="gzip",
    )
    logger.info("loaded pandas df from %s", filename)
    return df


# TODO: Is this required
def normalize_project_type_specifics(path: Path):
    """Explode nested json column project_type_specifics and drop empty columns."""
    df = pd.read_csv(path)

    if "project_type_specifics" in df.columns.tolist() and not is_numeric_dtype(df["project_type_specifics"]):
        # convert json string to json dict
        df["project_type_specifics"] = df["project_type_specifics"].map(json.loads)

        normalized = pd.json_normalize(
            typing.cast("list[dict[typing.Any, typing.Any]]", df["project_type_specifics"]),
        )
        normalized.index = df.index
        df = pd.concat([df, normalized], axis=1).drop(columns=["project_type_specifics"])
        for column in list(normalized.columns):
            if "properties" in column:
                df.rename(columns={column: column.replace("properties.", "")}, inplace=True)

    df.to_csv(path)


def write_sql_to_gzipped_csv(filename: Path, sql_query: sql.Composed | sql.SQL):
    """Use the copy statement to write data from postgres to a csv file."""
    with tempfile.NamedTemporaryFile(suffix=".csv", dir=Config.TEMP_DIR) as tmp_csv_file:
        with connection.cursor() as cursor:
            cursor.copy_expert(sql_query, tmp_csv_file)

        tmp_csv_file.seek(0)
        normalize_project_type_specifics(Path(tmp_csv_file.name))

        tmp_csv_file.seek(0)
        with gzip.open(filename, "wb") as f_out:
            f_out.writelines(tmp_csv_file)

        logger.info("wrote gzipped csv file from sql: %s", filename)

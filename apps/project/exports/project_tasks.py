import logging
from pathlib import Path

import pandas as pd
from psycopg2 import sql

from apps.project.models import Project, ProjectTask, ProjectTaskGroup
from utils.common import fd_name, tb_name

from .utils.common import load_df_from_csv, write_sql_to_gzipped_csv

logger = logging.getLogger(__name__)


def generate_project_tasks(
    *,
    destination_filename: Path,
    project: Project,
) -> pd.DataFrame:
    """Check if tasks have been downloaded already.
    If not: Query tasks from postgres database for project id and
    save tasks to a csv file.
    Then load pandas dataframe from this csv file.
    Return dataframe.
    """
    # TODO: what is this is already generated?

    # TODO: check zoom_level usages
    # TODO: use id or firebase_id for ids?

    # TODO: tile_x was taskX before (fix this for firebase sync)
    # TODO: tile_y was taskY before (fix this for firebase sync)

    sql_query = sql.SQL(
        f"""
        COPY (
            SELECT
                -- internal id
                PTG.{fd_name(ProjectTaskGroup.project_id)} as project_internal_id,
                PTG.{fd_name(ProjectTaskGroup.id)} as group_internal_id,
                PT.{fd_name(ProjectTask.id)} as task_internal_id,
                -- firebase id
                P.{fd_name(Project.firebase_id)} as project_id,
                PTG.{fd_name(ProjectTaskGroup.firebase_id)} as group_id,
                PT.{fd_name(ProjectTask.firebase_id)} as task_id,
                -- Metadata
                -- NOTE: Using ST_Multi only to make the exports backward compatible with previous exports
                ST_AsText(ST_Multi({fd_name(ProjectTask.geometry)})) AS geom,
                '{project.project_type_specifics.get("zoom_level")}' as tile_z,
                -- NOTE: Existing tile_x and tile_y are passed from project_type_specifics now
                -- NOTE: this is destructured by normalize_project_type_specifics(write_sql_to_gzipped_csv)
                PT.{fd_name(ProjectTask.project_type_specifics)}
            FROM {tb_name(ProjectTask)} PT
                LEFT JOIN {tb_name(ProjectTaskGroup)} PTG ON
                    PTG.id = PT.{fd_name(ProjectTask.task_group)}
                LEFT JOIN {tb_name(Project)} P ON
                    P.id = PTG.{fd_name(ProjectTaskGroup.project_id)}
            WHERE PTG.{fd_name(ProjectTaskGroup.project_id)} = {{}}
        ) TO STDOUT WITH CSV HEADER
        """,
    ).format(sql.Literal(project.id))

    write_sql_to_gzipped_csv(destination_filename, sql_query)

    df = load_df_from_csv(destination_filename)

    # Remove Unnamed column
    df = df.loc[:, ~df.columns.str.contains("Unnamed")]

    # TODO: Check this
    # Tasks for the "validate" project type can contain a "username" attribute.
    # We rename this attribute into "osm_username" to be able to distinguish it
    # later from the username of the MapSwipe user.
    # The optional OSM username in the tasks of the "validate" project type refers
    # to the OSM user who has last edited the OSM object.
    if "username" in df.columns:
        df.rename(columns={"username": "osm_username"}, inplace=True)
    return df

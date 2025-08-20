import logging
from pathlib import Path

import pandas as pd
from psycopg2 import sql

from apps.project.models import Project, ProjectTaskGroup
from utils.common import fd_name, tb_name

from .utils.common import load_df_from_csv, write_sql_to_gzipped_csv

logger = logging.getLogger(__name__)


def generate_project_task_groups(destination_filename: Path, project: Project) -> pd.DataFrame:
    """
    Check if groups have been downloaded already.
    If not: Query groups from postgres database for project id and
    save groups to a csv file.
    Then load pandas dataframe from this csv file.
    Return dataframe.
    """

    # TODO: check how we use number_of_users_required
    #   it can get you a wrong number, if more users finished than required
    # TODO: Use firebase id for group_id?
    sql_query = sql.SQL(
        f"""
        COPY (
            SELECT
                -- internal id
                PTG.{fd_name(ProjectTaskGroup.id)} as group_internal_id,
                PTG.{fd_name(ProjectTaskGroup.project_id)} as project_internal_id,
                -- firebase id
                PTG.{fd_name(ProjectTaskGroup.firebase_id)} as group_id,
                P.{fd_name(Project.firebase_id)} as project_id,
                -- Metadata
                PTG.{fd_name(ProjectTaskGroup.number_of_tasks)} as number_of_tasks,
                PTG.{fd_name(ProjectTaskGroup.required_count)} as required_count,
                PTG.{fd_name(ProjectTaskGroup.finished_count)} as finished_count,
                PTG.{fd_name(ProjectTaskGroup.progress)} as progress,
                PTG.{fd_name(ProjectTaskGroup.total_area)} as total_area,
                PTG.{fd_name(ProjectTaskGroup.time_spent_max_allowed)} as time_spent_max_allowed,
                (
                    PTG.{fd_name(ProjectTaskGroup.required_count)} +
                    PTG.{fd_name(ProjectTaskGroup.finished_count)}
                ) as number_of_users_required,
                -- NOTE: this is destructured by normalize_project_type_specifics(write_sql_to_gzipped_csv)
                PTG.{fd_name(ProjectTaskGroup.project_type_specifics)}
            FROM {tb_name(ProjectTaskGroup)} PTG
                LEFT JOIN {tb_name(Project)} P ON
                    P.id = PTG.{fd_name(ProjectTaskGroup.project_id)}
            WHERE PTG.{fd_name(ProjectTaskGroup.project_id)} = {{}}
        ) TO STDOUT WITH CSV HEADER
        """,
    ).format(sql.Literal(project.id))
    write_sql_to_gzipped_csv(destination_filename, sql_query)

    df = load_df_from_csv(destination_filename)
    return df.loc[:, ~df.columns.str.contains("Unnamed")]

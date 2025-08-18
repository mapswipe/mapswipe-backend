import datetime
import logging
from pathlib import Path

import pandas as pd
from psycopg2 import sql

from apps.contributor.models import ContributorUser
from apps.mapping.models import (
    MappingSession,
    MappingSessionResult,
)
from apps.project.models import Project, ProjectTask, ProjectTaskGroup
from utils.common import fd_name, tb_name

from .utils.common import load_df_from_csv, write_sql_to_gzipped_csv

logger = logging.getLogger(__name__)


def generate_mapping_results(*, destination_filename: Path, project: Project) -> pd.DataFrame:
    # TODO: client_type IS ENUM -- CONVERT TO VALUE?
    sql_query = sql.SQL(f"""
        COPY (
            SELECT
                -- internal id
                PTG.{fd_name(ProjectTaskGroup.project_id)} as project_internal_id,
                MS.{fd_name(MappingSession.project_task_group_id)} as group_internal_id,
                MSR.{fd_name(MappingSessionResult.project_task_id)} as task_internal_id,
                MS.{fd_name(MappingSession.contributor_user_id)} as user_internal_id,
                -- firebase id
                P.{fd_name(Project.firebase_id)} as project_id,
                PTG.{fd_name(ProjectTaskGroup.firebase_id)} as group_id,
                PT.{fd_name(ProjectTask.firebase_id)} as task_id,
                U.{fd_name(ContributorUser.firebase_id)} as user_id,
                -- Metadata
                MS.{fd_name(MappingSession.start_time)} as timestamp,
                MS.{fd_name(MappingSession.start_time)} as start_time,
                MS.{fd_name(MappingSession.end_time)} as end_time,
                MS.{fd_name(MappingSession.app_version)} as app_version,
                MS.{fd_name(MappingSession.client_type)} as client_type,
                MSR.{fd_name(MappingSessionResult.result)} as result,
                -- the username for users which login to MapSwipe with their
                -- OSM account is not defined or ''.
                -- We capture this here as it will cause problems
                -- for the user stats generation.
                CASE
                    WHEN
                        U.{fd_name(ContributorUser.username)} IS NULL OR
                        U.{fd_name(ContributorUser.username)} = '' THEN 'unknown'
                    ELSE U.{fd_name(ContributorUser.username)}
                END as username
            FROM {tb_name(MappingSessionResult)} MSR
                LEFT JOIN {tb_name(MappingSession)} MS ON
                    MS.id = MSR.{fd_name(MappingSessionResult.session_id)}
                LEFT JOIN {tb_name(ContributorUser)} U ON
                    U.id = MS.{fd_name(MappingSession.contributor_user_id)}
                LEFT JOIN {tb_name(ProjectTask)} PT ON
                    PT.id = MSR.{fd_name(MappingSessionResult.project_task_id)}
                LEFT JOIN {tb_name(ProjectTaskGroup)} PTG ON
                    PTG.id = MS.{fd_name(MappingSession.project_task_group_id)}
                LEFT JOIN {tb_name(Project)} P ON
                    P.id = PTG.{fd_name(ProjectTaskGroup.project_id)}
            WHERE PTG.{fd_name(ProjectTaskGroup.project_id)} = '{project.id}'
        ) TO STDOUT WITH CSV HEADER
    """)

    write_sql_to_gzipped_csv(destination_filename, sql_query)
    df = load_df_from_csv(destination_filename)

    # Remove Unnamed column
    df = df.loc[:, ~df.columns.str.contains("Unnamed")]

    if df.empty:
        logger.info("there are no results for this project %s", project.id)
    else:
        # TODO: Is this required?
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["day"] = df["timestamp"].apply(lambda x: datetime.datetime(year=x.year, month=x.month, day=x.day))
        logger.info("added day attribute for results for %s", project.id)
    return df

from django.db import connection
from psycopg2 import sql

from apps.mapping.models import MappingSession
from apps.project.models import Project, ProjectTaskGroup
from utils.common import fd_name, tb_name


# Source: https://github.com/mapswipe/python-mapswipe-workers/blob/e32dcb32410209dbf3a293218c5686d6b22ad88a/mapswipe_workers/mapswipe_workers/firebase_to_postgres/update_data.py#L570-L625
def calculate_project_progress(project: Project) -> int:
    """Calculate overall project progress as the average progress for all groups.
    This is not hundred percent exact, since groups can have a different number of tasks
    but it is still "good enough" and gives almost correct progress.
    But it is easier to compute than considering the actual number of tasks per group.

    NOTE: the cast to integer in postgres rounds decimals. This means that for 99.5%
    progress, we return 100% here. We should evaluate if this is what we want if/when
    we introduce automated project rotation upon completion (as the reported completion
    would happen 0.5% before actual completion).
    """
    sql_query = sql.SQL(
        f"""
        -- Get all groups for this project
        WITH relevant_groups AS (
            SELECT
                {fd_name(ProjectTaskGroup.id)} as id,
                {fd_name(ProjectTaskGroup.project_id)} as project_id
            FROM {tb_name(ProjectTaskGroup)}
            WHERE {fd_name(ProjectTaskGroup.project_id)} = %s
        ),
        -- add progress for groups that have been worked on already.
        -- Set progress to 0 if no user has worked on this group.
        -- For groups that no users worked on there are no entries in the results table.
        group_progress AS (
            SELECT
                ms.{fd_name(MappingSession.project_task_group_id)},
                -- Here we get the progress for all groups for which results have been submitted already.
                -- Progress for a group can be max 100 even if more users than required submitted results.
                -- The verification number of a project is used here.
                LEAST(
                    (
                        100
                        * COUNT(DISTINCT ms.{fd_name(MappingSession.contributor_user_id)})
                        / p.{fd_name(Project.verification_number)}
                    ),
                    100
                ) AS group_progress
            FROM {tb_name(MappingSession)} ms
                JOIN relevant_groups rg
                    ON ms.{fd_name(MappingSession.project_task_group_id)} = rg.id
                JOIN {tb_name(Project)} p
                    ON p.{fd_name(Project.id)} = rg.project_id
            GROUP BY
                ms.{fd_name(MappingSession.project_task_group_id)},
                p.{fd_name(Project.verification_number)}
        )
        SELECT
            COALESCE(
                AVG(COALESCE(gp.group_progress, 0)),
                0
            )::integer AS progress
        FROM relevant_groups rg
            LEFT JOIN group_progress gp ON gp.project_task_group_id = rg.id;
        """,
    )

    with connection.cursor() as cursor:
        cursor.execute(sql_query, (project.pk,))
        row = cursor.fetchall()
        return row[0][0]

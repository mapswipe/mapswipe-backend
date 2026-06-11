import csv
import logging
import typing
from pathlib import Path

import dateutil.parser
from django.db import connection, transaction

from apps.contributor.models import ContributorUser, ContributorUserGroup
from apps.mapping.models import (
    MappingSession,
    MappingSessionClientTypeEnum,
    MappingSessionResult,
    MappingSessionResultTemp,
    MappingSessionUserGroup,
    MappingSessionUserGroupTemp,
)

# import geojson
from apps.project.models import Project, ProjectTask, ProjectTaskGroup
from apps.project.tasks import generate_project_exports
from main.bulk_managers import BulkCreateManager
from main.config import Config
from main.logging import log_extra
from utils.common import fd_name, tb_name

logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from django.db.backends.utils import CursorWrapper


class FirebaseCleanupAlreadyDoneException(Exception): ...


class FirebaseCleanup:
    def __init__(self):
        # NOTE: We need to set value to None to clear the value in firebase
        self._mapping_sessions: dict[str, None] = {}
        # NOTE: We need to set value to None to clear the value in firebase
        self._root_project: dict[str, None] = {}
        self._done = False

    def _already_done_check(self):
        if self._done:
            raise FirebaseCleanupAlreadyDoneException("done already called")

    @staticmethod
    def _generate_ref_key(
        *,
        project_firebase_id: str,
        group_firebase_id: str,
        contributor_user_firebase_id: str,
    ):
        return f"{project_firebase_id}/{group_firebase_id}/{contributor_user_firebase_id}"

    def mark_as_delete(
        self,
        *,
        project_firebase_id: str,
        group_firebase_id: str,
        contributor_user_firebase_id: str,
    ):
        """Flags a contributor's mapping session data in a project group for deletion in Firebase."""
        self._already_done_check()
        key = self._generate_ref_key(
            project_firebase_id=project_firebase_id,
            group_firebase_id=group_firebase_id,
            contributor_user_firebase_id=contributor_user_firebase_id,
        )
        self._mapping_sessions[key] = None

    def undo_mark_as_delete(
        self,
        *,
        project_firebase_id: str,
        group_firebase_id: str,
        contributor_user_firebase_id: str,
    ):
        """Removes the deletion flag from a contributor's mapping session data within a project group in Firebase."""
        self._already_done_check()
        key = self._generate_ref_key(
            project_firebase_id=project_firebase_id,
            group_firebase_id=group_firebase_id,
            contributor_user_firebase_id=contributor_user_firebase_id,
        )
        if key in self._mapping_sessions:
            del self._mapping_sessions[key]

    def add_project(
        self,
        *,
        project_firebase_id: str,
    ):
        """⚠️ Use with caution!
        Flags all mapping sessions related to a project in Firebase for deletion.
        """
        self._already_done_check()
        self._root_project[project_firebase_id] = None

    def done(self):
        if self._mapping_sessions:
            logger.info("Cleanup up firebase results")

            project_firebase_ids = set([mapping_session.split("/")[0] for mapping_session in self._mapping_sessions])
            # Trigger generate_project_exports for updated projects
            for project_firebase_id in project_firebase_ids:
                transaction.on_commit(
                    # XXX: we loose type check with s (signature)
                    generate_project_exports.s(project_firebase_id=project_firebase_id).delay,
                )

            # clear keys from firebase
            Config.FIREBASE_HELPER.ref(Config.FirebaseKeys.results_projects()).update(self._mapping_sessions)
            logger.info("Cleared firebase results")

        if self._root_project:
            for project_firebase_id in self._root_project:
                logger.warning("Cleanup up firebase results by project: %s", project_firebase_id)
            # clear keys from firebase
            Config.FIREBASE_HELPER.ref(Config.FirebaseKeys.results_projects()).update(self._root_project)
            logger.info("Cleared firebase results by project")

        self._done = True


def dict_iterator(dict_: dict[object, object]):
    return dict_.items()


def list_iterator(list_: list[object]):
    return enumerate(list_)


def results_complete(
    mapping_session_data: dict[str, typing.Any],
    project_firebase_id: str,
    group_firebase_id: str,
    contributor_user_firebase_id: str,
    required_attributes: list[str],
) -> bool:
    """Check if all attributes are set."""
    complete = True
    for attribute in required_attributes:
        if attribute not in mapping_session_data:
            complete = False
            logger.error(
                "missing mapping_sessions attribute '%s' ",
                attribute,
                extra=log_extra(
                    dict(
                        project_firebase_id=project_firebase_id,
                        group_firebase_id=group_firebase_id,
                        contributor_user_firebase_id=contributor_user_firebase_id,
                    ),
                ),
            )
    return complete


SQL_QUERY_TO_PRE_FILL_TEMP_TABLE_DATA_REF_COLUMNS = f"""
    WITH processed AS (
        SELECT
            RT.{fd_name(MappingSessionResultTemp.id)} as mapping_session_id,
            -- Ref
            PTG.{fd_name(ProjectTaskGroup.id)} as project_task_group_id,
            PT.{fd_name(ProjectTask.id)} as project_task_id,
            CU.{fd_name(ContributorUser.id)} as contributor_user_id
        FROM
            {tb_name(MappingSessionResultTemp)} RT
                -- Project
                LEFT JOIN {tb_name(Project)} P ON
                    P.{fd_name(Project.firebase_id)} = RT.{fd_name(MappingSessionResultTemp.project_firebase_id)}
                -- Project Task Group
                LEFT JOIN {tb_name(ProjectTaskGroup)} PTG ON
                    PTG.{fd_name(ProjectTaskGroup.firebase_id)} = RT.{fd_name(MappingSessionResultTemp.group_firebase_id)} AND
                    PTG.{fd_name(ProjectTaskGroup.project)} = P.{fd_name(Project.id)}
                -- Project Task
                LEFT JOIN {tb_name(ProjectTask)} PT ON
                    PT.{fd_name(ProjectTask.firebase_id)} = RT.{fd_name(MappingSessionResultTemp.task_firebase_id)} AND
                    PT.{fd_name(ProjectTask.task_group)} = PTG.{fd_name(ProjectTaskGroup.id)}
                -- Contributor User
                LEFT JOIN {tb_name(ContributorUser)} CU ON
                    CU.{fd_name(ContributorUser.firebase_id)} = RT.{fd_name(MappingSessionResultTemp.contributor_user_firebase_id)}
    )
    UPDATE {tb_name(MappingSessionResultTemp)}
    SET
        {fd_name(MappingSessionResultTemp.group_id)} = processed.project_task_group_id,
        {fd_name(MappingSessionResultTemp.task_id)} = processed.project_task_id,
        {fd_name(MappingSessionResultTemp.contributor_user_id)} = processed.contributor_user_id,
        {fd_name(MappingSessionResultTemp.is_firebase_mapping_valid)} = (
            -- XXX: We only need to check contributor_user_id, others are generated from backend
            processed.project_task_group_id is not NULL
            AND processed.project_task_id is not NULL
            AND processed.contributor_user_id is not NULL
        )
    FROM processed
    WHERE
        {tb_name(MappingSessionResultTemp)}.{fd_name(MappingSessionResultTemp.id)} = processed.mapping_session_id;
"""  # noqa: E501


SQL_QUERY_TO_TRANSFER_TEMP_TABLE_DATA_TO_MAPPING_SESSIONS = f"""
    INSERT INTO {tb_name(MappingSession)} (
        -- Ref
        {fd_name(MappingSession.project_task_group)},
        {fd_name(MappingSession.contributor_user_id)},
        -- Swipe Metadata (Aggregates)
        {fd_name(MappingSession.start_time)},
        {fd_name(MappingSession.end_time)},
        {fd_name(MappingSession.items_count)},
        -- Device metadata
        {fd_name(MappingSession.app_version)},
        {fd_name(MappingSession.client_type)}
    ) (
        SELECT
            -- Ref
            RT.{fd_name(MappingSessionResultTemp.group_id)},                -- project_task_group_id
            RT.{fd_name(MappingSessionResultTemp.contributor_user_id)},     -- contributor_user_id
            -- Swipe Metadata (Aggregates)
            min(RT.{fd_name(MappingSessionResultTemp.start_time)}),      -- start_time
            max(RT.{fd_name(MappingSessionResultTemp.end_time)}),        -- end_time
            COUNT(*),                                                    -- items_count
            -- Device metadata
            RT.{fd_name(MappingSessionResultTemp.app_version)},          -- app_version
            RT.{fd_name(MappingSessionResultTemp.client_type)}           -- client_type
        FROM
            {tb_name(MappingSessionResultTemp)} RT
        WHERE
            RT.{fd_name(MappingSessionResultTemp.is_firebase_mapping_valid)} is True
        GROUP BY
            RT.{fd_name(MappingSessionResultTemp.group_id)},
            RT.{fd_name(MappingSessionResultTemp.contributor_user_id)},
            RT.{fd_name(MappingSessionResultTemp.app_version)},
            RT.{fd_name(MappingSessionResultTemp.client_type)}
    )
    ON CONFLICT (
         {fd_name(MappingSession.project_task_group)},
         {fd_name(MappingSession.contributor_user)}
    )
    DO NOTHING;
"""


SQL_QUERY_TO_TRANSFER_TEMP_TABLE_DATA_TO_MAPPING_SESSION_RESULTS = f"""
    INSERT INTO {tb_name(MappingSessionResult)} (
        -- Ref
        {fd_name(MappingSessionResult.session)},
        {fd_name(MappingSessionResult.project_task)},
        -- Value
        {fd_name(MappingSessionResult.result)},
        {fd_name(MappingSessionResult.task_partition_index)}
    ) (
        SELECT
            -- Ref
            MS.{fd_name(MappingSession.id)},               -- mapping_session_id
            RT.{fd_name(MappingSessionResultTemp.task_id)},   -- task_id
            -- Value
            RT.{fd_name(MappingSessionResultTemp.result)},  -- result [TODO: ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(RT.result), 3857), 4326)]
            RT.{fd_name(MappingSessionResultTemp.task_partition_index)}  -- task partition index
        FROM {tb_name(MappingSessionResultTemp)} RT
            LEFT JOIN {tb_name(MappingSession)} MS ON
                MS.{fd_name(MappingSession.project_task_group)} = RT.{fd_name(MappingSessionResultTemp.group_id)} AND
                MS.{fd_name(MappingSession.contributor_user)} = RT.{fd_name(MappingSessionResultTemp.contributor_user_id)}
        WHERE
            RT.{fd_name(MappingSessionResultTemp.is_firebase_mapping_valid)} is True
    )
    ON CONFLICT (
        {fd_name(MappingSessionResult.session)},
        {fd_name(MappingSessionResult.project_task)},
        {fd_name(MappingSessionResult.task_partition_index)}
    )
    DO NOTHING;
"""  # noqa: E501


# FIXME(tnagorra): this crashes when user_group is not defined
SQL_QUERY_TO_TRANSFER_TEMP_TABLE_DATA_TO_MAPPING_SESSION_USER_GROUP = f"""
    INSERT INTO {tb_name(MappingSessionUserGroup)} (
         {fd_name(MappingSessionUserGroup.mapping_session)},
         {fd_name(MappingSessionUserGroup.user_group)}
    ) (
        SELECT
            MS.{fd_name(MappingSession.id)},                    -- mapping_session
            UG.{fd_name(ContributorUserGroup.id)}               -- user_group
        FROM {tb_name(MappingSessionUserGroupTemp)} UGRT
            -- Project
            LEFT JOIN {tb_name(Project)} P ON
                P.{fd_name(Project.firebase_id)} = UGRT.{fd_name(MappingSessionUserGroupTemp.project_firebase_id)}
            -- Project Task Group
            LEFT JOIN {tb_name(ProjectTaskGroup)} PTG ON
                PTG.{fd_name(ProjectTaskGroup.firebase_id)} = UGRT.{fd_name(MappingSessionUserGroupTemp.group_firebase_id)} AND
                PTG.{fd_name(ProjectTaskGroup.project)} = P.{fd_name(Project.id)}
            -- Contributor User
            LEFT JOIN {tb_name(ContributorUser)} CU ON
                CU.{fd_name(ContributorUser.firebase_id)} = UGRT.{fd_name(MappingSessionUserGroupTemp.contributor_user_firebase_id)}
            -- Mapping Session
            LEFT JOIN {tb_name(MappingSession)} MS ON
                MS.{fd_name(MappingSession.project_task_group)} = PTG.{fd_name(ProjectTaskGroup.id)} AND
                MS.{fd_name(MappingSession.contributor_user)} = CU.{fd_name(ContributorUser.id)}
            -- Contributor User Group
            LEFT JOIN {tb_name(ContributorUserGroup)} UG ON
                UG.{fd_name(ContributorUserGroup.firebase_id)} = UGRT.{fd_name(MappingSessionUserGroupTemp.user_group_firebase_id)}
        WHERE
            MS.{fd_name(MappingSession.id)} is not NULL
    )
    ON CONFLICT (
         {fd_name(MappingSessionUserGroup.mapping_session)},
         {fd_name(MappingSessionUserGroup.user_group)}
    )
    DO NOTHING;
"""  # noqa: E501


def cleanup_temp_tables(cursor: "CursorWrapper | None" = None):
    def _cleanup(_cursor: "CursorWrapper"):
        logger.info("Cleaning up staging results")
        _cursor.execute(f"TRUNCATE TABLE {tb_name(MappingSessionResultTemp)} RESTART IDENTITY;")
        _cursor.execute(f"TRUNCATE TABLE {tb_name(MappingSessionUserGroupTemp)} RESTART IDENTITY;")
        logger.info("Cleared staging results")

    if cursor is not None:
        _cleanup(cursor)
        return

    with connection.cursor() as cursor_:
        _cleanup(cursor_)


def process_invalid_temp_results(
    firebase_cleanup: FirebaseCleanup,
):
    base_qs = MappingSessionResultTemp.objects.filter(is_firebase_mapping_valid=False)

    invalid_results_count = base_qs.count()
    if invalid_results_count == 0:
        return

    logger.warning("%s results has been flagged as invalid", invalid_results_count)

    # Add unsynced user to firebase, which will be processed by the user sync task
    invalid_user_firebase_ids = (
        base_qs.filter(contributor_user_id__isnull=True).values_list("contributor_user_firebase_id", flat=True).distinct()
    )
    for invalid_user_firebase_id in invalid_user_firebase_ids:
        logger.warning(
            "Adding %s to the firebase user update %s",
            invalid_user_firebase_id,
            Config.FirebaseKeys.contributor_user_updates(),
        )
        Config.FIREBASE_HELPER.ref(
            Config.FirebaseKeys.contributor_user_update(invalid_user_firebase_id),
        ).set(True)

    # Skip firebase cleanup for invalid mapping data
    invalid_result_temp_qs = base_qs.values_list(
        "project_firebase_id",
        "group_firebase_id",
        "contributor_user_firebase_id",
    ).distinct()

    for project_firebase_id, group_firebase_id, contributor_user_firebase_id in invalid_result_temp_qs:
        firebase_cleanup.undo_mark_as_delete(
            project_firebase_id=project_firebase_id,
            group_firebase_id=group_firebase_id,
            contributor_user_firebase_id=contributor_user_firebase_id,
        )

    try:
        # NOTE: For debugging, store the latest invalid dataset to internal directory
        with Path.open(
            Config.InternalDir.LAST_RUN_MAPPING_SESSION_INVALID_DATA,
            "w",
            newline="",
            encoding="utf-8",
        ) as f:
            fields = [f.name for f in MappingSessionResultTemp._meta.fields]

            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()

            for row in base_qs.values(*fields).iterator(chunk_size=2000):
                writer.writerow(row)
            logger.info("Stored invalid mapping data to %s", Config.InternalDir.LAST_RUN_MAPPING_SESSION_INVALID_DATA)
    except Exception:
        logger.error(
            "Failed to generate mapping session invalid data export to internal directory",
            exc_info=True,
        )


def transfer_results_from_temp_tables(
    firebase_cleanup: FirebaseCleanup,
):
    with transaction.atomic(), connection.cursor() as cursor:
        logger.info("Processing mapping sessions temp table data")
        cursor.execute(SQL_QUERY_TO_PRE_FILL_TEMP_TABLE_DATA_REF_COLUMNS)
        logger.info("Transferring staging results to real tables")
        logger.info("Creating mapping sessions")
        cursor.execute(SQL_QUERY_TO_TRANSFER_TEMP_TABLE_DATA_TO_MAPPING_SESSIONS)
        logger.info("Creating mapping sessions results")
        cursor.execute(SQL_QUERY_TO_TRANSFER_TEMP_TABLE_DATA_TO_MAPPING_SESSION_RESULTS)
        logger.info("Creating mapping sessions for contributor user groups")
        cursor.execute(SQL_QUERY_TO_TRANSFER_TEMP_TABLE_DATA_TO_MAPPING_SESSION_USER_GROUP)
        logger.info("Transferred staging results to real tables")

        process_invalid_temp_results(firebase_cleanup)

        cleanup_temp_tables(cursor)


def results_to_temp_table(
    bulk_create_manager: BulkCreateManager,
    firebase_cleanup: FirebaseCleanup,
    project: Project,
    group_results: dict[str, typing.Any],
    # result_type: str = "integer",
):
    """Move results from firebase to temporary table.

    - projects
      - groups (group_results)
        - users (Mapping session)
          results
            - tasks: value
    """
    logger.info("project %s: Start transfer results to staging area", project.firebase_id)
    logger.info("project %s: Got %s groups", project.firebase_id, len(group_results.items()))

    for group_firebase_id, users_results in group_results.items():
        for contributor_user_firebase_id, mapping_session_data in users_results.items():
            firebase_cleanup.mark_as_delete(
                project_firebase_id=project.firebase_id,
                group_firebase_id=group_firebase_id,
                contributor_user_firebase_id=contributor_user_firebase_id,
            )

            # check if all attributes are set
            # if not don't transfer the results for this group
            if not results_complete(
                mapping_session_data,
                project.firebase_id,
                group_firebase_id,
                contributor_user_firebase_id,
                required_attributes=["startTime", "endTime", "results"],
            ):
                continue

            # Mapping session attributes
            start_time = dateutil.parser.parse(mapping_session_data["startTime"])
            end_time = dateutil.parser.parse(mapping_session_data["endTime"])
            if start_time > end_time:
                logger.error(
                    "mapping_sessions: start time is greater then end time",
                    extra=log_extra(
                        {
                            "start_time": start_time,
                            "end_time": end_time,
                        },
                    ),
                )
                continue

            app_version = mapping_session_data.get("appVersion", "")
            client_type = MappingSessionClientTypeEnum.get_client_type(
                mapping_session_data.get("clientType"),
            )

            session_results = mapping_session_data["results"]
            if not session_results:
                logger.error("mapping_sessions: results(task/value map) is empty")
                continue

            if type(session_results) is dict:
                session_results_iterator = dict_iterator(session_results)
            elif type(session_results) is list:
                # TODO: optimize for performance?
                # (make sure data from firebase is always a dict)
                # if key is a integer firebase will return a list
                # if first key (list index) is 5
                # list indices 0-4 will have value None
                session_results_iterator = list_iterator(session_results)
            else:
                logger.error(
                    "mapping_sessions: invalid results(task/value map)",
                    extra=log_extra(
                        {
                            "results": session_results,
                        },
                    ),
                )
                continue

            # Collect results for each tasks
            for task_firebase_id, result in session_results_iterator:
                if result is None:
                    # TODO: Do we treat it as 0?
                    logger.error("mapping_sessions: results task value is None")
                    continue

                # This was used for DIGITIZATION
                # if result_type == "geometry":
                #     result = geojson.dumps(geojson.GeometryCollection(result))

                # NOTE [Important]:
                # If the result is a list (e.g. Locate Objects project),
                # example: result = [1, 0, 0, 1]
                # Each index represents a partition of the same task.
                # We create one row per partition using:
                #   task_partition_index = list index
                #   result = value at that index
                #
                # Example:
                #   result = [1, 0, 0, 1]
                #   -> (partition 0, value 1)
                #   -> (partition 1, value 0)
                #   -> (partition 2, value 0)
                #   -> (partition 3, value 1)
                #
                # For non-list results (fallback to default),
                # task_partition_index defaults to 0.

                results_list = result if isinstance(result, list) else [result]
                for index, result_value in enumerate(results_list):
                    bulk_create_manager.add(
                        MappingSessionResultTemp(
                            task_partition_index=index,
                            project_firebase_id=project.firebase_id,
                            group_firebase_id=group_firebase_id,
                            contributor_user_firebase_id=contributor_user_firebase_id,
                            task_firebase_id=task_firebase_id,
                            start_time=start_time,
                            end_time=end_time,
                            result=result_value,
                            app_version=app_version,
                            client_type=client_type,
                        ),
                    )

            # Tag this session to all user groups mentioned
            for user_group_firebase_id, is_selected in mapping_session_data.get("userGroups", {}).items():
                if not is_selected:
                    continue
                bulk_create_manager.add(
                    MappingSessionUserGroupTemp(
                        project_firebase_id=project.firebase_id,
                        group_firebase_id=group_firebase_id,
                        contributor_user_firebase_id=contributor_user_firebase_id,
                        user_group_firebase_id=user_group_firebase_id,
                    ),
                )

    logger.info("project %s: Copied data to temp tables", project.firebase_id)

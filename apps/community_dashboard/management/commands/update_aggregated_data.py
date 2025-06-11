import datetime
import time
import typing

from django.core.management.base import BaseCommand
from django.db import connection, models, transaction
from django.utils import timezone

from apps.community_dashboard.models import (
    AggregatedTracking,
    AggregatedTrackingTypeEnum,
    AggregatedUserGroupStatData,
    AggregatedUserStatData,
)
from apps.mapping.models import MappingSession, MappingSessionUserGroup
from apps.project.models import Project, ProjectTaskGroup, ProjectTypeEnum


def tb_name(model: type[models.Model]) -> str:
    return model._meta.db_table


# FIXME(thenav56): Add typing for the field
def fd_name(field: typing.Any) -> str:
    return field.field.column


UPDATE_USER_DATA_SQL = f"""
    INSERT INTO "{tb_name(AggregatedUserStatData)}" (
        {fd_name(AggregatedUserGroupStatData.project)},
        {fd_name(AggregatedUserGroupStatData.user)},
        {fd_name(AggregatedUserGroupStatData.timestamp_date)},
        {fd_name(AggregatedUserGroupStatData.total_time)},
        {fd_name(AggregatedUserGroupStatData.task_count)},
        {fd_name(AggregatedUserGroupStatData.area_swiped)},
        {fd_name(AggregatedUserGroupStatData.swipes)}
    )
    (
        -- Data by user
        WITH user_data AS (
            SELECT
                P.{fd_name(Project.id)} AS project_id,
                P.{fd_name(Project.project_type)} AS project_type,
                MS.{fd_name(MappingSession.contributor_user)} AS user_id,
                MS.{fd_name(MappingSession.start_time)}::date AS timestamp_date,
                MS.{fd_name(MappingSession.items_count)} AS task_count,
                Coalesce(
                    (
                        CASE
                            -- Hide area for Footprint TODO: Replace 2 with ProjectTypeEnum.FOOTPRINT.value
                            WHEN P.{fd_name(Project.project_type)} = 2 THEN 0
                            ELSE PTG.{fd_name(ProjectTaskGroup.total_area)}
                        END
                    )
                ) AS area_swiped,
                LEAST(
                    EXTRACT(
                        EPOCH FROM (
                            MS.{fd_name(MappingSession.end_time)} - MS.{fd_name(MappingSession.start_time)}
                        )
                    ),
                    PTG.{fd_name(ProjectTaskGroup.time_spent_max_allowed)}
                ) AS time_spent_sec
            FROM {tb_name(MappingSession)} MS
                LEFT JOIN {tb_name(ProjectTaskGroup)} PTG
                    ON PTG.id = MS.{fd_name(MappingSession.project_task_group)}
                LEFT JOIN {tb_name(Project)} P
                    ON P.id = PTG.{fd_name(ProjectTaskGroup.project)}
            WHERE
                MS.{fd_name(MappingSession.start_time)} >= %(from_date)s AND
                MS.{fd_name(MappingSession.start_time)} < %(until_date)s
        ),
        aggregate_user_data AS (
            SELECT
                project_id,
                project_type,
                user_id,
                timestamp_date,
                COALESCE(SUM(time_spent_sec), 0) AS total_time,
                COALESCE(SUM(task_count), 0) AS task_count,
                COALESCE(SUM(area_swiped), 0) AS area_swiped
            FROM user_data
            GROUP BY
                project_id, project_type, user_id, timestamp_date
        )
        -- Final data adjustments
        SELECT
            project_id,
            user_id,
            timestamp_date,
            total_time,
            task_count,
            area_swiped,
            CASE
                WHEN project_type in (
                    {ProjectTypeEnum.FIND.value},
                    {ProjectTypeEnum.COMPLETENESS.value}
                ) THEN ROUND(task_count / 6)
                ELSE task_count
            END AS swipes
        FROM aggregate_user_data
    )
    ON CONFLICT
        (project_id, user_id, timestamp_date)
    DO UPDATE SET
        total_time = EXCLUDED.total_time,
        task_count = EXCLUDED.task_count,
        swipes = EXCLUDED.swipes,
        area_swiped = EXCLUDED.area_swiped;
"""

UPDATE_USER_GROUP_SQL = f"""
    INSERT INTO "{tb_name(AggregatedUserGroupStatData)}" (
        {fd_name(AggregatedUserGroupStatData.project)},
        {fd_name(AggregatedUserGroupStatData.user)},
        {fd_name(AggregatedUserGroupStatData.user_group)},
        {fd_name(AggregatedUserGroupStatData.timestamp_date)},
        {fd_name(AggregatedUserGroupStatData.total_time)},
        {fd_name(AggregatedUserGroupStatData.task_count)},
        {fd_name(AggregatedUserGroupStatData.area_swiped)},
        {fd_name(AggregatedUserGroupStatData.swipes)}
    )
    (
        -- Data by user
        with user_group_data AS (
            SELECT
                P.{fd_name(Project.id)} AS project_id,
                P.{fd_name(Project.project_type)} AS project_type,
                MS.{fd_name(MappingSession.contributor_user)} AS user_id,
                MSUG.{fd_name(MappingSessionUserGroup.user_group)} AS user_group_id,
                MS.{fd_name(MappingSession.start_time)}::date AS timestamp_date,
                MS.{fd_name(MappingSession.items_count)} AS task_count,
                Coalesce(
                    (
                        CASE
                            -- Hide area for Footprint TODO: Replace 2 with ProjectTypeEnum.FOOTPRINT.value
                            WHEN P.{fd_name(Project.project_type)} = 2 THEN 0
                            ELSE PTG.{fd_name(ProjectTaskGroup.total_area)}
                        END
                    )
                ) AS area_swiped,
                LEAST(
                    EXTRACT(
                        EPOCH FROM (
                            MS.{fd_name(MappingSession.end_time)} - MS.{fd_name(MappingSession.start_time)}
                        )
                    ),
                    PTG.{fd_name(ProjectTaskGroup.time_spent_max_allowed)}
                ) AS time_spent_sec
            FROM {tb_name(MappingSessionUserGroup)} MSUG
                LEFT JOIN {tb_name(MappingSession)} MS
                    ON MS.{fd_name(MappingSession.id)} = MSUG.{fd_name(MappingSessionUserGroup.mapping_session)}
                LEFT JOIN {tb_name(ProjectTaskGroup)} PTG
                    ON PTG.id = MS.{fd_name(MappingSession.project_task_group)}
                LEFT JOIN {tb_name(Project)} P
                    ON P.id = PTG.{fd_name(ProjectTaskGroup.project)}
            WHERE
                MS.{fd_name(MappingSession.start_time)} >= %(from_date)s AND
                MS.{fd_name(MappingSession.start_time)} < %(until_date)s
        ),
        aggregate_user_group_data AS (
            SELECT
                project_id,
                project_type,
                user_id,
                user_group_id,
                timestamp_date,
                COALESCE(SUM(time_spent_sec), 0) AS total_time,
                COALESCE(SUM(task_count), 0) AS task_count,
                COALESCE(SUM(area_swiped), 0) AS area_swiped
            FROM user_group_data
            GROUP BY
                project_id, project_type, user_id, user_group_id, timestamp_date
        )
        -- Final data adjustments
        SELECT
            project_id,
            user_id,
            user_group_id,
            timestamp_date,
            total_time,
            task_count,
            area_swiped,
            CASE
                WHEN project_type in (
                    {ProjectTypeEnum.FIND.value},
                    {ProjectTypeEnum.COMPLETENESS.value}
                ) THEN ROUND(task_count / 6)
                ELSE task_count
            END AS swipes
        FROM aggregate_user_group_data
    )
    ON CONFLICT
        (project_id, user_id, user_group_id, timestamp_date)
    DO UPDATE SET
        total_time = EXCLUDED.total_time,
        task_count = EXCLUDED.task_count,
        swipes = EXCLUDED.swipes,
        area_swiped = EXCLUDED.area_swiped;
"""

INTERVAL_RANGE_DAYS = 30


class Command(BaseCommand):
    def _track(self, tracker_type: AggregatedTrackingTypeEnum, label: str, sql: str):
        tracker, _ = AggregatedTracking.objects.get_or_create(type=tracker_type)
        now = timezone.now().date()
        # Fallback: For now only update from 1 day before instead of whole data
        # which is quite big.
        from_date = tracker.value
        if tracker.value is not None:
            from_date = datetime.datetime.strptime(tracker.value, "%Y-%m-%d").date()
        else:
            timestamp_min = MappingSession.objects.aggregate(timestamp_min=models.Min("start_time"))["timestamp_min"]
            if timestamp_min:
                self.stdout.write(f"Using min timestamps from database {timestamp_min}")
                from_date = timestamp_min.date()
            else:
                self.stdout.write("Nothing found from database.")
                from_date = now
        while True:
            until_date = min(
                now,
                from_date + datetime.timedelta(days=INTERVAL_RANGE_DAYS),
            )
            if from_date >= until_date:
                self.stdout.write(f"{label.title()} Nothing to do here.....")
                break
            params = dict(
                from_date=from_date.strftime("%Y-%m-%d"),
                until_date=until_date.strftime("%Y-%m-%d"),
            )
            start_time = time.time()

            self.stdout.write(f"Updating {label.title()} Data for date: {params}")
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(sql, params)
                self.stdout.write(self.style.SUCCESS(f"Successful. Runtime: {time.time() - start_time} seconds"))
                tracker.value = from_date = until_date
                self.stdout.write(f"Saving date {tracker.value} as last tracker")
                tracker.save()

    def run(self):
        self._track(
            AggregatedTrackingTypeEnum.USER_DATA_LATEST_DATE,
            "user",
            UPDATE_USER_DATA_SQL,
        )
        self._track(
            AggregatedTrackingTypeEnum.USER_GROUP_DATA_LATEST_DATE,
            "user_group",
            UPDATE_USER_GROUP_SQL,
        )

    @typing.override
    def handle(self, **_):
        self.run()

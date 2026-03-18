import logging
import typing

from celery import signals
from celery.schedules import crontab
from django.db import models
from kombu import Queue
from sentry_sdk.integrations.celery import beat as sentry_celery_beat

if typing.TYPE_CHECKING:
    from celery import Celery
    from sentry_sdk._types import MonitorConfig  # type: ignore[reportPrivateImportUsage]

logger = logging.getLogger(__name__)


class TimeConstants:
    SECONDS_IN_A_DAY = 24 * 60 * 60
    SECONDS_IN_A_HOUR = 60 * 60
    SECONDS_IN_A_WEEK = 7 * 24 * 60 * 60
    SECONDS_IN_A_MINUTE = 60

    EVERY_WEEK = crontab(minute="1", hour="1", day_of_week="1")
    EVERY_DAY = crontab(minute="1", hour="1")
    EVERY_HOUR = crontab(minute="0", hour="*")
    EVERY_2_MINUTES = crontab(minute="*/2")
    EVERY_1_MINUTES = crontab(minute="*/1")


class CeleryQueue:
    # NOTE: Make sure all queue names are lowercase (They are in k8s)
    default = Queue("default")

    ALL_QUEUE = (default,)


class CronJobOption(typing.TypedDict, total=False):
    # https://docs.celeryq.dev/en/latest/reference/celery.app.task.html#celery.app.task.Task.apply_async

    expire_seconds: float
    """
    Seconds in the future for the task should expire.
    The task won't be executed after the expiration time.
    """

    time_limit: int
    soft_time_limit: int


class CeleryBeatSchedule(typing.TypedDict):
    task: str
    schedule: crontab
    options: CronJobOption
    args: tuple[typing.Any, ...] | None


class CronJobSentryConfig(typing.NamedTuple):
    checkin_margin: int = 5  # In min grace period
    """
    The amount of time (in minutes) Sentry should wait for your check-in before it's considered missed ("grace period").
    Optional.
    """

    max_runtime: int = 30  # In min
    """The amount of time (in minutes) your job is allowed to run before it's considered failed. Optional."""

    failure_issue_threshold: int = 1
    """The number of consecutive failed check-ins it takes before an issue is created. Optional."""

    recovery_threshold: int = 1
    """The number of consecutive OK check-ins it takes before an issue is resolved. Optional."""

    def as_dict(self) -> "MonitorConfig":
        return {
            "checkin_margin": self.checkin_margin,
            "max_runtime": self.max_runtime,
            "failure_issue_threshold": self.failure_issue_threshold,
            "recovery_threshold": self.recovery_threshold,
        }


class CronJob(typing.NamedTuple):
    task: str
    schedule: crontab
    args: tuple[typing.Any, ...] | None = None
    sentry_config: CronJobSentryConfig = CronJobSentryConfig()
    options: CronJobOption = {}


# NOTE: PeriodicTask will be delete from database if removed from here
SCHEDULES: dict[str, CronJob] = {
    "clear_expired_django_sessions": CronJob(
        task="apps.common.tasks.clear_expired_django_sessions",
        schedule=TimeConstants.EVERY_WEEK,
        options=CronJobOption(expire_seconds=TimeConstants.SECONDS_IN_A_WEEK),
    ),
    "pull_users_from_firebase": CronJob(
        task="apps.contributor.tasks.pull_users_from_firebase_task",
        schedule=TimeConstants.EVERY_1_MINUTES,
        options=CronJobOption(expire_seconds=TimeConstants.SECONDS_IN_A_MINUTE),
        sentry_config=CronJobSentryConfig(
            failure_issue_threshold=10,
            checkin_margin=2,
            max_runtime=2,
        ),
    ),
    "pull_user_group_memberships_from_firebase_task": CronJob(
        task="apps.contributor.tasks.pull_user_group_memberships_from_firebase_task",
        schedule=TimeConstants.EVERY_2_MINUTES,
        options=CronJobOption(expire_seconds=TimeConstants.SECONDS_IN_A_MINUTE * 2),
        sentry_config=CronJobSentryConfig(
            failure_issue_threshold=10,
            checkin_margin=2,
            max_runtime=2,
        ),
    ),
    "pull_mapping_session_from_firebase": CronJob(
        task="apps.mapping.tasks.pull_mapping_session_from_firebase",
        schedule=TimeConstants.EVERY_2_MINUTES,
        options=CronJobOption(expire_seconds=TimeConstants.SECONDS_IN_A_MINUTE * 2),
        sentry_config=CronJobSentryConfig(
            failure_issue_threshold=10,
            checkin_margin=2,
            max_runtime=2,
        ),
    ),
    "regenerate_global_project_assets": CronJob(
        task="apps.project.tasks.regenerate_global_project_assets",
        schedule=TimeConstants.EVERY_HOUR,
        options=CronJobOption(expire_seconds=TimeConstants.SECONDS_IN_A_HOUR),
        sentry_config=CronJobSentryConfig(
            failure_issue_threshold=2,
            checkin_margin=2,
            max_runtime=2,
        ),
    ),
    "update_community_dashboard_aggregated_data": CronJob(
        task="apps.community_dashboard.tasks.update_aggregated_data",
        schedule=TimeConstants.EVERY_DAY,
        options=CronJobOption(expire_seconds=TimeConstants.SECONDS_IN_A_DAY),
        sentry_config=CronJobSentryConfig(
            failure_issue_threshold=1,
            checkin_margin=10,
            max_runtime=10,
        ),
    ),
    # Queue uptime
    **{
        f"celery_queue_uptime_{celery_queue.name}": CronJob(
            task="apps.common.tasks.celery_queue_uptime_check",
            args=(celery_queue.name,),
            schedule=TimeConstants.EVERY_HOUR,
            options=CronJobOption(expire_seconds=TimeConstants.SECONDS_IN_A_HOUR),
            sentry_config=CronJobSentryConfig(
                failure_issue_threshold=2,
                checkin_margin=2,
                max_runtime=2,
            ),
        )
        for celery_queue in CeleryQueue.ALL_QUEUE
    },
}

BEAT_SCHEDULES: dict[str, CeleryBeatSchedule] = {
    name: {
        "task": config.task,
        "args": config.args,
        "schedule": config.schedule,
        "options": config.options,
    }
    for name, config in SCHEDULES.items()
}


_get_monitor_config = sentry_celery_beat._get_monitor_config  # type: ignore[reportPrivateUsage]


class SentryMonkeyPatch:
    @staticmethod
    def custom__get_monitor_config(celery_schedule: typing.Any, app: "Celery", monitor_name: str) -> "MonitorConfig":
        """Get configuration for sentry monitoring.

        https://github.com/getsentry/sentry-python/blob/5715734eac1c5fb4b6ec61ef459080c74fa777b5/sentry_sdk/integrations/celery/beat.py#L59
        """
        config = _get_monitor_config(celery_schedule, app, monitor_name)
        job_config = SCHEDULES.get(monitor_name)
        if job_config:
            # Adding additional custom configs
            config.update(job_config.sentry_config.as_dict())
        return config


sentry_celery_beat._get_monitor_config = SentryMonkeyPatch.custom__get_monitor_config  # type: ignore[reportPrivateUsage]


@signals.beat_init.connect
def update_periodic_tasks(**_):
    logger.info("Cronjob sync: Start")
    try:
        from django_celery_beat.models import PeriodicTask  # noqa: PLC0415

        base_tasks_qs = PeriodicTask.objects.filter(
            task__startswith="apps.",  # Our tasks
        )

        obsolete_tasks_qs = base_tasks_qs.exclude(
            models.Q(
                name__in=list(BEAT_SCHEDULES.keys()),
            )
            | models.Q(
                name__startswith="manual:",  # Lets filter-out if it has `manual:` at the start
            ),
        )

        logger.info("Cronjob sync - Obsolete tasks: Start")
        obsolete_tasks = list(obsolete_tasks_qs)
        if obsolete_tasks:
            for task in obsolete_tasks:
                logger.warning("Cronjob Sync - Obsolete tasks: Task <%s> will be deleted", task.name)

            deleted_periodic_task = obsolete_tasks_qs.delete()
            logger.warning("Cronjob Sync - Obsolete tasks: Deleted %s tasks ", deleted_periodic_task)
        else:
            logger.info("Cronjob Sync - Obsolete tasks: Nothing to do")

    except Exception:
        logger.error("Cronjob Sync: Failed to sync PeriodicTasks", exc_info=True)

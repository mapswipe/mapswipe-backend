import typing

from celery.schedules import crontab
from sentry_sdk.integrations.celery import beat as sentry_celery_beat

if typing.TYPE_CHECKING:
    from celery import Celery
    from sentry_sdk._types import MonitorConfig  # type: ignore[reportPrivateImportUsage]


class CeleryBeatSchedule(typing.TypedDict):
    task: str
    schedule: crontab


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
    sentry_config: CronJobSentryConfig = CronJobSentryConfig()


# NOTE: PeriodicTask will be delete from database if removed from here
SCHEDULES: dict[str, CronJob] = {
    "clear_expired_django_sessions": CronJob(
        task="apps.common.tasks.clear_expired_django_sessions",
        schedule=crontab(minute="1", hour="1", day_of_week="1"),
    ),
    "pull_users_from_firebase": CronJob(
        task="apps.contributor.tasks.pull_users_from_firebase_task",
        schedule=crontab(minute="*/1"),  # Every 1 minutes
        sentry_config=CronJobSentryConfig(
            failure_issue_threshold=10,
            checkin_margin=2,
            max_runtime=2,
        ),
    ),
    "pull_user_group_memberships_from_firebase_task": CronJob(
        task="apps.contributor.tasks.pull_user_group_memberships_from_firebase_task",
        schedule=crontab(minute="*/2"),  # Every 2 minutes
        sentry_config=CronJobSentryConfig(
            failure_issue_threshold=10,
            checkin_margin=2,
            max_runtime=2,
        ),
    ),
    "pull_mapping_session_from_firebase": CronJob(
        task="apps.mapping.tasks.pull_mapping_session_from_firebase",
        schedule=crontab(minute="*/2"),  # Every 2 minutes
        sentry_config=CronJobSentryConfig(
            failure_issue_threshold=10,
            checkin_margin=2,
            max_runtime=2,
        ),
    ),
    "regenerate_global_project_assets": CronJob(
        task="apps.project.tasks.regenerate_global_project_assets",
        schedule=crontab(hour="*"),  # Every hour
        sentry_config=CronJobSentryConfig(
            failure_issue_threshold=2,
            checkin_margin=2,
            max_runtime=2,
        ),
    ),
}

BEAT_SCHEDULES: dict[str, CeleryBeatSchedule] = {
    name: {
        "task": config.task,
        "schedule": config.schedule,
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

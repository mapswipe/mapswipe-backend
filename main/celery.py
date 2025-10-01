import logging
import os
import typing
from logging.config import dictConfig
from typing import TYPE_CHECKING

import celery
from celery import signals
from django.conf import settings
from django.db import models
from kombu import Queue

from .cronjobs import BEAT_SCHEDULES

if TYPE_CHECKING:
    from celery.app.task import Task

    from main.sentry import SentryConfig

    Task.__class_getitem__ = classmethod(lambda cls, *args, **kwargs: cls)  # type: ignore[attr-defined]

logger = logging.getLogger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")


class CeleryQueue:
    # NOTE: Make sure all queue names are lowercase (They are in k8s)
    default = Queue("default")

    ALL_QUEUE = (default,)


class Celery(celery.Celery):
    def on_configure(self):  # type: ignore[reportIncompatibleVariableOverride]
        if settings.SENTRY_ENABLED:
            sentry_config: SentryConfig = settings.SENTRY_CONFIG
            sentry_config.init_sentry()


app = Celery("main")
app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.task_default_queue = CeleryQueue.default.name
app.conf.task_queues = CeleryQueue.ALL_QUEUE

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.beat_schedule = BEAT_SCHEDULES


@signals.setup_logging.connect
def config_loggers(**_):
    from django.conf import settings

    dictConfig(settings.LOGGING)


@signals.beat_init.connect
def clean_up_periodic_tasks(**_):
    try:
        from django_celery_beat.models import PeriodicTask  # type: ignore[reportMissingTypeStubs]

        obsolute_tasks_qs = PeriodicTask.objects.filter(
            task__startswith="apps.",  # Our tasks
        ).exclude(
            models.Q(
                name__in=list(BEAT_SCHEDULES.keys()),
            )
            | models.Q(
                name__startswith="manual:",  # Lets filter-out if it has `manual:` at the start
            ),
        )

        obsolute_tasks = list(obsolute_tasks_qs)
        if obsolute_tasks:
            for task in obsolute_tasks:
                logger.warning("Task to delete: %s", task.name)

            deleted_periodic_task = obsolute_tasks_qs.delete()
            logger.warning("Deleted tasks not defined in the codebase: %s", deleted_periodic_task)
    except Exception:
        logger.error("Failed to clean-up PeriodicTasks", exc_info=True)


@app.task(bind=True, ignore_result=True)
def debug_task(self: "Task[typing.Any, typing.Any]"):
    logger.info("Request: %s", self.request)

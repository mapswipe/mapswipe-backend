import logging
import os
import typing
from logging.config import dictConfig
from typing import TYPE_CHECKING

import celery
from celery import signals
from django.conf import settings

from .cronjobs import BEAT_SCHEDULES, CeleryQueue

if TYPE_CHECKING:
    from celery.app.task import Task

    from main.sentry import SentryConfig

    Task.__class_getitem__ = classmethod(lambda cls, *args, **kwargs: cls)  # type: ignore[attr-defined]

logger = logging.getLogger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")


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


@app.task(bind=True, ignore_result=True)
def debug_task(self: "Task[typing.Any, typing.Any]"):
    logger.info("Request: %s", self.request)

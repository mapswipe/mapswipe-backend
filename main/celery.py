import logging
import os
from logging.config import dictConfig
from typing import TYPE_CHECKING

import celery
from celery import signals
from celery.schedules import crontab
from django.conf import settings
from kombu import Queue

if TYPE_CHECKING:
    from main.sentry import SentryConfig

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

app.conf.beat_schedule = {
    "apps.common.clear_expired_django_sessions": {
        "task": "apps.common.clear_expired_django_sessions",
        "schedule": crontab(minute="1", hour="1", day_of_week="1"),
        "options": {"queue": "default"},
    },
}


@signals.setup_logging.connect
def config_loggers(**_):
    from django.conf import settings

    dictConfig(settings.LOGGING)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    logger.info("Request: %s", self.request)

import logging
import os

import celery
from celery.schedules import crontab
from django.conf import settings
from kombu import Queue

from main.sentry import SentryConfig

logger = logging.getLogger(__name__)


class Celery(celery.Celery):
    def on_configure(self):
        if settings.SENTRY_ENABLED:
            sentry_config: SentryConfig = settings.SENTRY_CONFIG
            sentry_config.init_sentry()


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")

app = Celery("main")

app.conf.beat_schedule = {
    "apps.common.clear_expired_django_sessions": {
        "task": "apps.common.clear_expired_django_sessions",
        "schedule": crontab(minute="1", hour="1", day_of_week="monday"),
        "options": {"queue": "default"},
    },
}


class CeleryQueue:
    # NOTE: Make sure all queue names are lowercase (They are in k8s)
    default = Queue("default")

    ALL_QUEUE = (default,)


# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.task_default_queue = CeleryQueue.default.name

app.conf.task_queues = CeleryQueue.ALL_QUEUE


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")

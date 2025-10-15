import logging

from celery import shared_task
from django.core import management

from main.cache import CeleryLock

logger = logging.getLogger(__name__)


class InvalidObjectPushException(Exception): ...


@shared_task
def clear_expired_django_sessions():
    with CeleryLock.redis_lock(CeleryLock.Key.CLEAR_EXPIRED_DJANGO_SESSIONS) as acquired:
        if not acquired:
            logger.warning("Clear expired django sessions")
            return
        management.call_command("clearsessions", verbosity=0)


@shared_task
def celery_queue_uptime_check(queue: str):
    logger.info("Celery Queue %s is taking task...", queue)

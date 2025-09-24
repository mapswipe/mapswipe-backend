import logging

from celery import shared_task

from apps.mapping.firebase.pull import pull_results_from_firebase
from main.cache import CeleryLock
from main.cronjobs import TimeConstants

logger = logging.getLogger(__name__)


@shared_task
def pull_mapping_session_from_firebase():
    with CeleryLock.redis_lock(
        CeleryLock.Key.MAPPING_SESSION_PULL_FROM_FIREBASE,
        lock_expire=TimeConstants.SECONDS_IN_A_HOUR,  # Lock for an hour
    ) as acquired:
        if not acquired:
            logger.warning("Mapping Session Pull from Firebase already running")
            return

    pull_results_from_firebase()

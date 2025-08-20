import logging

from celery import shared_task

from apps.mapping.firebase.firebase import pull_results_from_firebase
from main.cache import CeleryLock

logger = logging.getLogger(__name__)


@shared_task
def pull_mapping_session_from_firebase():
    with CeleryLock.redis_lock(CeleryLock.Key.MAPPING_SESSION_PULL_FROM_FIREBASE) as acquired:
        if not acquired:
            logger.warning("Mapping Session Pull from Firebase already running")
            return

    pull_results_from_firebase()

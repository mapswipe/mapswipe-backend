import logging

from celery import shared_task

from apps.contributor.firebase.pull import pull_user_group_memberships_from_firebase, pull_users_from_firebase
from main.cache import CeleryLock

logger = logging.getLogger(__name__)


@shared_task
def pull_users_from_firebase_task():
    with CeleryLock.redis_lock(CeleryLock.Key.USERS_PULL_FROM_FIREBASE) as acquired:
        if not acquired:
            logger.warning("Pull users from firebase is already running")
            return

    pull_users_from_firebase()


@shared_task
def pull_user_group_memberships_from_firebase_task():
    with CeleryLock.redis_lock(CeleryLock.Key.USER_GROUP_MEMBERSHIPS_PULL_FROM_FIREBASE) as acquired:
        if not acquired:
            logger.warning("Pull user group memberships from firebase is already running")
            return

    pull_user_group_memberships_from_firebase()

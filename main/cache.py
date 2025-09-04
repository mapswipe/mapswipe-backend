import time
from contextlib import contextmanager

from django.conf import settings
from django.core.cache import caches
from django_redis.client import DefaultClient

cache: DefaultClient = caches["default"]  # type: ignore[reportAssignmentType]


class CeleryLock:
    class Key:
        CLEAR_EXPIRED_DJANGO_SESSIONS = "CLEAR_EXPIRED_DJANGO_SESSIONS"

        # FIXME(tnagorra): Rename this to project process task
        PROJECT_LOAD_GEOMETRY = "PROJECT_LOAD_GEOMETRY_{0}"
        # FIXME(tnagorra): Rename this to project push to firebase
        PUSH_PROJECT_TO_FIREBASE = "PUSH_PROJECT_TO_FIREBASE_{0}"
        PROJECT_EXPORTS_GENERATE = "PROJECT_GENERATE_EXPORTS_{0}"

        TUTORIAL_PUSH_TO_FIREBASE = "TUTORIAL_PUSH_TO_FIREBASE_{0}"

        MAPPING_SESSION_PULL_FROM_FIREBASE = "MAPPING_SESSION_PULL_FROM_FIREBASE"

        USERS_PULL_FROM_FIREBASE = "USERS_PULL_FROM_FIREBASE"
        USER_GROUP_MEMBERSHIPS_PULL_FROM_FIREBASE = "USER_GROUP_MEMBERSHIPS_PULL_FROM_FIREBASE"

        GLOBAL_PROJECT_ASSETS = "GLOBAL_PROJECT_ASSETS"

    @staticmethod
    @contextmanager
    def redis_lock(lock_id: str):
        timeout_at: float = time.monotonic() + settings.REDIS_LOCK_EXPIRE - 3
        # cache.add fails if the key already exists
        status = cache.add(lock_id, 1, settings.REDIS_LOCK_EXPIRE)
        try:
            yield status
        finally:
            # memcache delete is very slow, but we have to use it to take
            # advantage of using add() for atomic locking
            if time.monotonic() < timeout_at and status:
                # don't release the lock if we exceeded the timeout
                # to lessen the chance of releasing an expired lock
                # owned by someone else
                # also don't release the lock if we didn't acquire it
                cache.delete(lock_id)

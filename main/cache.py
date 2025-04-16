import time
from contextlib import contextmanager

from django.conf import settings
from django.core.cache import caches
from django_redis.client import DefaultClient

cache: DefaultClient = caches["default"]  # type: ignore[reportAssignmentType]


class CeleryLock:
    class Key:
        CLEAR_EXPIRED_DJANGO_SESSIONS = "CLEAR_EXPIRED_DJANGO_SESSIONS"
        PROJECT_LOAD_GEOMETRY = "PROJECT_LOAD_GEOMETRY_{0}"

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

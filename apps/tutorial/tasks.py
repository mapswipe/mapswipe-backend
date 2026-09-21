import logging

from celery import current_task, shared_task

from apps.tutorial.models import Tutorial
from main.cache import CeleryLock
from project_types.store import get_tutorial_type_handler

logger = logging.getLogger(__name__)


@shared_task
def push_tutorial_to_firebase(tutorial_id: int):
    with CeleryLock.redis_lock(CeleryLock.Key.TUTORIAL_PUSH_TO_FIREBASE.format(tutorial_id)) as acquired:
        if not acquired:
            # NOTE: Another push for this tutorial is currently running. Retry (capped
            # backoff, up to 5 attempts) instead of dropping this push immediately: the
            # lock is only ever held for the duration of one push, so a few retries
            # should be enough. After 5 retries, current_task.retry() raises
            # MaxRetriesExceededError instead of scheduling another one, surfacing a
            # real task failure instead of retrying forever.
            countdown = min(2**current_task.request.retries, 30)
            logger.warning(
                "Tutorial(id: %s) push tutorial to firebase already running, retrying in %ss",
                tutorial_id,
                countdown,
            )
            raise current_task.retry(countdown=countdown, max_retries=5)

        tutorial = Tutorial.objects.get(pk=tutorial_id)
        tutorial_type_handler = get_tutorial_type_handler(tutorial.project.project_type_enum)(tutorial)
        tutorial_type_handler.push_tutorial_on_firebase()
        return True

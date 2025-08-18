import logging

from celery import shared_task

from apps.common.firebase import FirebasePush
from apps.common.models import FirebasePushStatusEnum
from apps.tutorial.models import Tutorial
from main.cache import CeleryLock
from project_types.store import get_tutorial_type_handler
from utils.celery import RetryableTask

logger = logging.getLogger(__name__)


@shared_task(bind=True, base=RetryableTask)
def push_tutorial_to_firebase(self: RetryableTask, tutorial_id: int):
    with CeleryLock.redis_lock(CeleryLock.Key.TUTORIAL_PUSH_TO_FIREBASE.format(tutorial_id)) as acquired:
        if not acquired:
            logger.warning("Tutorial(id: %s) push tutorial to firebase already running", tutorial_id)
            return None

    tutorial = Tutorial.objects.get(pk=tutorial_id)
    tutorial_type_handler = get_tutorial_type_handler(tutorial.project.project_type_enum)(tutorial)
    try:
        tutorial_type_handler.push_tutorial_on_firebase()
    except Exception as exc:
        tutorial.update_firebase_push_status(FirebasePushStatusEnum.PENDING)
        FirebasePush.handle_firebase_push_error(
            exc,
            self,
            Tutorial,
            FirebasePush.MAX_RETRY_LIMIT,
            FirebasePush.MIN_RETRY_DELAY,
            FirebasePush.MAX_RETRY_DELAY,
            tutorial.id,
        )
    return True

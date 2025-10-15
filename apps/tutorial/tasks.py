import logging

from celery import shared_task

from apps.tutorial.models import Tutorial
from main.cache import CeleryLock
from project_types.store import get_tutorial_type_handler

logger = logging.getLogger(__name__)


@shared_task
def push_tutorial_to_firebase(tutorial_id: int):
    with CeleryLock.redis_lock(CeleryLock.Key.TUTORIAL_PUSH_TO_FIREBASE.format(tutorial_id)) as acquired:
        if not acquired:
            logger.warning("Tutorial(id: %s) push tutorial to firebase already running", tutorial_id)
            return None

        tutorial = Tutorial.objects.get(pk=tutorial_id)
        tutorial_type_handler = get_tutorial_type_handler(tutorial.project.project_type_enum)(tutorial)
        tutorial_type_handler.push_tutorial_on_firebase()
        return True

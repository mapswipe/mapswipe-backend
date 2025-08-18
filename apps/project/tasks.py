import logging

from celery import shared_task

from apps.common.firebase import FirebasePush
from apps.common.models import FirebasePushStatusEnum
from apps.project.models import Project
from main.cache import CeleryLock
from project_types.store import get_project_type_handler
from utils.celery import RetryableTask

logger = logging.getLogger(__name__)


@shared_task
def process_project_task(project_id: int):
    with CeleryLock.redis_lock(CeleryLock.Key.PROJECT_LOAD_GEOMETRY.format(project_id)) as acquired:
        if not acquired:
            logger.warning("Project(id: %s) geometry load is already running", project_id)
            return None

    project = Project.objects.get(pk=project_id)
    try:
        project_type_handler = get_project_type_handler(project.project_type_enum)(project)
        project_type_handler.process_project()
        return True
    except Exception:
        logger.error("Project geometry load failed", exc_info=True)
        project.update_status(Project.Status.FAILED, True)
        return False


@shared_task(bind=True, base=RetryableTask)
def push_project_to_firebase(self: RetryableTask, project_id: int):
    with CeleryLock.redis_lock(CeleryLock.Key.PUSH_PROJECT_TO_FIREBASE.format(project_id)) as acquired:
        if not acquired:
            logger.warning("Project(id: %s) push project to firebase already running", project_id)
            return None

    project = Project.objects.get(pk=project_id)
    project_type_handler = get_project_type_handler(project.project_type_enum)(project)
    try:
        project_type_handler.push_project_on_firebase()
    except Exception as exc:
        project.update_firebase_push_status(FirebasePushStatusEnum.PENDING)
        FirebasePush.handle_firebase_push_error(
            exc,
            self,
            Project,
            FirebasePush.MAX_RETRY_LIMIT,
            FirebasePush.MIN_RETRY_DELAY,
            FirebasePush.MAX_RETRY_DELAY,
            project.id,
        )
    return True


# TODO: How to trigger this? Scheduled or trigger by pull_mapping_session_from_firebase task?
@shared_task
def generate_project_exports(
    project_id: int | None = None,
    project_firebase_id: int | None = None,
):
    if project_id is not None:
        project = Project.objects.get(pk=project_id)
    elif project_firebase_id is not None:
        project = Project.objects.get(firebase_id=project_firebase_id)
    else:
        logger.error("generate_project_exports: Both project_id and project_firebase_id are none")
        return None

    with CeleryLock.redis_lock(CeleryLock.Key.PROJECT_EXPORTS_GENERATE.format(project.id)) as acquired:
        if not acquired:
            logger.warning("Project(id: %s) exports generate already running", project.id)
            return None

    project_type_handler = get_project_type_handler(project.project_type_enum)(project)
    project_type_handler.generate_exports()
    return True

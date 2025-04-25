import logging

from celery import shared_task

from apps.project.models import Project
from apps.project.project_types.store import get_project_type_handler
from main.cache import CeleryLock

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

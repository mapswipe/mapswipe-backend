import logging

from celery import shared_task

from apps.project.models import Project
from apps.project.project_types.store import get_project_type_handler
from main.cache import CeleryLock

logger = logging.getLogger(__name__)


@shared_task
def load_project_geometry(project_id: int):
    with CeleryLock.redis_lock(CeleryLock.Key.PROJECT_LOAD_GEOMETRY.format(project_id)) as acquired:
        if not acquired:
            logger.warning("Project(id: %s) geometry load is already running", project_id)
            return None

    project = Project.objects.get(pk=project_id)
    try:
        project_type_handler = get_project_type_handler(project.project_type)(project)
        project_type_handler.save_project()
        # TODO(thenav56): project.update_status(ProjectStatusEnum.GEOMETRY_LOADED)
        return True
    except Exception:
        logger.error("Project geometry load failed", exc_info=True)
        # TODO(thenav56): project.update_status(ProjectStatusEnum.FAILED)
        return False

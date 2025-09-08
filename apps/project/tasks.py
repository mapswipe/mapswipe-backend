import logging

from celery import shared_task

from apps.project.exports import overall_stats
from apps.project.models import Project
from apps.project.slack_messages import SlackMessage, base_slack_message, check_slack_thread, update_base_message
from main.cache import CeleryLock
from project_types.store import get_project_type_handler
from utils.slack import MapswipeSlack

logger = logging.getLogger(__name__)


@shared_task
def process_project_task(project_id: int):
    with CeleryLock.redis_lock(CeleryLock.Key.PROJECT_LOAD_GEOMETRY.format(project_id)) as acquired:
        if not acquired:
            logger.warning("Project(id: %s) processing is already running", project_id)
            return None

    project = Project.objects.get(pk=project_id)
    project_type_handler = get_project_type_handler(project.project_type_enum)(project)
    project_type_handler.process_project()
    return True


@shared_task
def push_project_to_firebase(project_id: int):
    with CeleryLock.redis_lock(CeleryLock.Key.PUSH_PROJECT_TO_FIREBASE.format(project_id)) as acquired:
        if not acquired:
            logger.warning("Project(id: %s) push project to firebase already running", project_id)
            return None

    project = Project.objects.get(pk=project_id)
    project_type_handler = get_project_type_handler(project.project_type_enum)(project)
    project_type_handler.push_project_on_firebase()
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


@shared_task
def regenerate_global_project_assets():
    with CeleryLock.redis_lock(CeleryLock.Key.GLOBAL_PROJECT_ASSETS) as acquired:
        if not acquired:
            logger.warning("regenerate_global_project_assets already running")
            return None

    overall_stats.generate()
    return True


@shared_task
def progress_change_message(project_id: int):
    project = Project.objects.get(pk=project_id)
    mapslack = MapswipeSlack()
    message = SlackMessage.get_message_for_project_progress(project=project)
    ts = check_slack_thread(project_id=project_id, mapslack=mapslack)
    reply_broadcast = project.progress >= 90
    if reply_broadcast:
        mapslack.send_slack_message(**message, thread_ts=ts, reply_broadcast=reply_broadcast)
    update_base_message(client=mapslack, project=project, ts=ts)


@shared_task
def status_update_message(project_id: int):
    project = Project.objects.get(pk=project_id)
    mapslack = MapswipeSlack()
    message = SlackMessage.get_message_for_status_update(
        project=project,
    )
    ts = check_slack_thread(project_id=project_id, mapslack=mapslack)
    mapslack.send_slack_message(**message, thread_ts=ts, reply_broadcast=False)
    update_base_message(client=mapslack, project=project, ts=ts)


@shared_task
def creation_success_message(project_id: int):
    mapslack = MapswipeSlack()
    base_slack_message(project_id=project_id, mapslack=mapslack)
    status_update_message.delay(project_id=project_id)

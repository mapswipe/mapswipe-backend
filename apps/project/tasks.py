import logging
from typing import Literal, assert_never

from celery import shared_task

from apps.project.exports import overall_stats
from apps.project.models import Project
from apps.project.slack_messages import (
    SlackMessage,
    get_or_create_base_slack_message,
    update_base_slack_message,
)
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
def send_slack_message_for_project(project_id: int, action: Literal["progress-change"] | Literal["status-change"]):
    mapslack = MapswipeSlack()
    project = Project.objects.get(pk=project_id)

    match action:
        case "progress-change":
            message = SlackMessage.get_message_for_project_progress(project=project)
        case "status-change":
            message = SlackMessage.get_message_for_project_status(project=project)
        case _:
            assert_never(action)

    # Create a base message if it doesn't exist
    base_slack_message_ts = get_or_create_base_slack_message(project_id=project_id, mapslack=mapslack)

    if not base_slack_message_ts:
        base_slack_message_ts = "mock_ts"

    # FIXME(tnagorra): What does reply_broadcast do?
    mapslack.send_slack_message(**message, thread_ts=base_slack_message_ts, reply_broadcast=False)
    update_base_slack_message(client=mapslack, project=project, ts=base_slack_message_ts)

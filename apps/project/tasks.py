import logging

from celery import shared_task

from apps.project.exports import overall_stats
from apps.project.models import Project
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
class SlackMessage:
    @classmethod
    async def get_message(
        cls,
        input_data: Project,
    ) -> MapswipeSlack.MapswipeSlackMessageArgumentType:
        if input_data.progress == 100:
            text = "Project reached 100%"
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "GREAT! PROJECT REACHED 100%  :tada:",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Congratulations on completing the project!",
                    },
                },
                {
                    "type": "divider",
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"_*Project Name:* {input_data.topic} - {input_data.region} ({input_data.project_number}) {input_data.requesting_organization.name}",  # noqa: E501
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": "https://pbs.twimg.com/profile_images/625633822235693056/lNGUneLX_400x400.jpg",
                        "alt_text": "cute cat",
                    },
                },
                {
                    "type": "divider",
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "You can now set this project to _'finished'_ and create a another one.",
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Visit Dashboard",
                            "emoji": True,
                        },
                        "value": "manager-dashboard",
                        "url": "https://managers.mapswipe.org/",
                        "action_id": "button-action",
                    },
                },
            ]
            return {
                "text": text,
                "blocks": blocks,
            }

        if 90 <= input_data.progress < 100:
            text = "Progress reached 90%"
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "ALMOST THERE! PROJECT REACHED 90% :hourglass_flowing_sand:",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "The project is almost at completion!",
                    },
                },
                {
                    "type": "divider",
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"_*Project Name:* {input_data.topic} - {input_data.region} ({input_data.project_number}) {input_data.requesting_organization.name} \n",  # noqa: E501
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": "https://pbs.twimg.com/profile_images/625633822235693056/lNGUneLX_400x400.jpg",
                        "alt_text": "cute cat",
                    },
                },
                {
                    "type": "divider",
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Get your next projects ready.",
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Visit Dashboard",
                            "emoji": True,
                        },
                        "value": "manager-dashboard",
                        "url": "https://managers.mapswipe.org/",
                        "action_id": "button-action",
                    },
                },
            ]
            return {
                "text": text,  # Required fallback
                "blocks": blocks,
            }

        return {"text": "", "blocks": []}


async def mapswipe_send_message(data: Project):
    mapslack = MapswipeSlack()
    message = await SlackMessage.get_message(input_data=data)
    await mapslack.send_slack_message(**message)

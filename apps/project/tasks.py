import logging
from datetime import datetime
from typing import TypedDict

from celery import shared_task
from django.conf import settings

from apps.project.exports import overall_stats
from apps.project.models import Project
from apps.user.models import User
from main.cache import CeleryLock
from project_types.store import get_project_type_handler
from utils.common import get_absolute_file_url
from utils.slack import MapswipeSlack


class BaseProjectArgs(TypedDict):
    project_name: str
    project_id: int
    project_type: int
    tutorial_id: int | None
    requesting_organization: str
    created_by: User
    created_at: datetime
    cover_image: str
    is_private: bool
    progress: int


class ProgressMessageArgs(BaseProjectArgs): ...


class StatusUpdateMessageArgs(BaseProjectArgs):
    modified_by: User
    modified_at: datetime


class CreationMessageArgs(BaseProjectArgs): ...


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
    manager_dashboard_block = {
        "accessory": {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "Visit Dashboard",
                "emoji": True,
            },
            "value": "manager-dashboard",
            "url": settings.MANAGER_DASHBOARD_DOMAIN.geturl(),
            "action_id": "button-action",
        },
    }

    @staticmethod
    def project_info_block(
        project_name: str,
        project_id: int,
        project_type: int,
        tutorial_id: int | None,
        requesting_organization: str,
        created_by: User,
        created_at: datetime,
        cover_image: str,
        progress: int,
        is_private: bool = True,
    ) -> dict:
        manager_dashboard_url = settings.MANAGER_DASHBOARD_DOMAIN.geturl()
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"Project Name: <{manager_dashboard_url}/project/{project_id}/edit|{project_name}>\n"
                    f"Project ID: {project_id}\n"
                    f"Project Type: {project_type}\n"
                    f"Tutorial: <{manager_dashboard_url}/tutorials/{tutorial_id}/edit|Tutorial Link>\n"
                    f"Tutorial ID: {tutorial_id}\n"
                    f"Requesting Organization: {requesting_organization}\n"
                    f"Created By: {created_by}\n"
                    f"Created At: {created_at.strftime('%b. %d, %Y, %-I:%M %p')}\n"
                    f"Progress: {progress}%\n\n"
                    f"{'This is a private project :lock:' if is_private else ''}\n"
                ),
            },
            "accessory": {
                "type": "image",
                "image_url": cover_image,
                "alt_text": "Project Cover Image",
            },
        }

    @classmethod
    def get_message_for_project_progress(
        cls,
        project_name: str,
        project_id: int,
        project_type: int,
        tutorial_id: int | None,
        requesting_organization: str,
        created_by: User,
        created_at: datetime,
        progress: int,
        cover_image: str,
        is_private: bool,
    ) -> MapswipeSlack.MapswipeSlackMessageArgumentType:
        if progress == 100:
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
                SlackMessage.project_info_block(
                    project_name,
                    project_id,
                    project_type,
                    tutorial_id,
                    requesting_organization,
                    created_by,
                    created_at,
                    cover_image,
                    progress,
                    is_private,
                ),
                {
                    "type": "divider",
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "You can now set this project to _'finished'_ and create a another one.",
                    },
                    **cls.manager_dashboard_block,
                },
            ]
            return {
                "text": text,
                "blocks": blocks,
            }

        if 90 <= progress < 100:
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
                SlackMessage.project_info_block(
                    project_name,
                    project_id,
                    project_type,
                    tutorial_id,
                    requesting_organization,
                    created_by,
                    created_at,
                    cover_image,
                    progress,
                    is_private,
                ),
                {
                    "type": "divider",
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Get your next projects ready.",
                    },
                    **cls.manager_dashboard_block,
                },
            ]
            return {
                "text": text,
                "blocks": blocks,
            }
        text = "Project Progress"
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"ALMOST THERE! PROJECT REACHED {progress}% :hourglass_flowing_sand:",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "The project is almost at completion!",
                },
            },
        ]

        return {
            "text": "Project Progress",
            "blocks": blocks,
        }

    @classmethod
    def get_message_for_project_creation(
        cls,
        project_name: str,
        project_id: int,
        project_type: int,
        tutorial_id: int | None,
        requesting_organization: str,
        created_by: User,
        created_at: datetime,
        cover_image: str,
        is_private: bool,
        progress: int,
    ) -> MapswipeSlack.MapswipeSlackMessageArgumentType:
        text = "Project Creation Successful"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "PROJECT CREATION SUCCESSFUL :confetti_ball:",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Congratulations on creating a new project!",
                },
            },
            {"type": "divider"},
            SlackMessage.project_info_block(
                project_name,
                project_id,
                project_type,
                tutorial_id,
                requesting_organization,
                created_by,
                created_at,
                cover_image,
                progress,
                is_private,
            ),
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "The project is published and now active. Happy Swiping! :slightly_smiling_face: :mapswipe:",
                },
                **cls.manager_dashboard_block,
            },
        ]

        return {
            "text": text,
            "blocks": blocks,
        }

    @classmethod
    def get_message_for_status_update(
        cls,
        project_name: str,
        project_id: int,
        project_type: int,
        tutorial_id: int | None,
        requesting_organization: str,
        created_by: User,
        created_at: datetime,
        modified_by: User,
        modified_at: datetime,
        cover_image: str,
        is_private: bool,
        progress: int,
    ) -> MapswipeSlack.MapswipeSlackMessageArgumentType:
        created_user_slack_id = created_by.slack_user_id
        modified_user_slack_id = modified_by.slack_user_id
        text = "Project status updated"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "PROJECT STATUS UPDATED :mapswipe:",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Hey <@{created_user_slack_id}>. The status of the project you created has been updated by <@{modified_user_slack_id}> at {modified_at.strftime('%b. %d, %Y, %-I:%M %p')}",  # noqa: E501
                },
            },
            {"type": "divider"},
            SlackMessage.project_info_block(
                project_name,
                project_id,
                project_type,
                tutorial_id,
                requesting_organization,
                created_by,
                created_at,
                cover_image,
                progress,
                is_private,
            ),
            {
                "type": "divider",
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Please visit the manager dashboard if you want to change the status of the project or create another one :mapswipe:",  # noqa: E501
                },
                **cls.manager_dashboard_block,
            },
        ]
        return {
            "text": text,
            "blocks": blocks,
        }


def base_message_args(project: Project) -> BaseProjectArgs:
    return {
        "project_name": project.generate_name(),
        "project_id": project.id,
        "project_type": project.project_type,
        "tutorial_id": project.tutorial_id,
        "requesting_organization": project.requesting_organization.name,
        "created_by": project.created_by,
        "created_at": project.created_at,
        "cover_image": (
            get_absolute_file_url(project.image.file)
            if project.image
            else "https://pbs.twimg.com/profile_images/625633822235693056/lNGUneLX_400x400.jpg"
        ),
        "is_private": project.is_private,
        "progress": project.progress,
    }


def status_message_args(project: Project) -> StatusUpdateMessageArgs:
    return {
        **base_message_args(project),
        "modified_by": project.modified_by,
        "modified_at": project.modified_at,
    }


def progress_message_args(project: Project) -> ProgressMessageArgs:
    return {
        **base_message_args(project),
    }


def creation_message_args(project: Project) -> CreationMessageArgs:
    return {
        **base_message_args(project),
    }


@shared_task
def send_message_for_progress(project_id: int):
    project = Project.objects.get(pk=project_id)
    mapslack = MapswipeSlack()
    message = SlackMessage.get_message_for_project_progress(**progress_message_args(project))
    mapslack.send_slack_message(**message, thread_ts=project.slack_thread_ts, reply_broadcast=True)
    update_message = SlackMessage.get_message_for_project_creation(
        **creation_message_args(project),
    )
    mapslack.update_slack_message(ts=project.slack_thread_ts, **update_message)


@shared_task
def project_status_update_message(project_id: int):
    project = Project.objects.get(pk=project_id)
    mapslack = MapswipeSlack()
    message = SlackMessage.get_message_for_status_update(**status_message_args(project))
    mapslack.send_slack_message(**message, thread_ts=project.slack_thread_ts, reply_broadcast=True)


@shared_task
def project_creation_success_message(project_id: int):
    project = Project.objects.get(pk=project_id)
    mapslack = MapswipeSlack()
    message = SlackMessage.get_message_for_project_creation(**creation_message_args(project))
    slack_response = mapslack.send_slack_message(**message)
    project.slack_thread_ts = slack_response.get("ts")
    project.save(update_fields=("slack_thread_ts",))

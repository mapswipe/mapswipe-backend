from apps.common.utils import get_absolute_uri
from apps.project.models import Project, ProjectStatusEnum, ProjectTypeEnum
from apps.user.models import User
from main.config import Config
from utils.slack import MapswipeSlack


class SlackMessage:
    @staticmethod
    def project_info_block(
        project: Project,
    ) -> dict:
        def generate_progress_bar(progress: int, bar_length: int = 10) -> str:
            filled_length = int(bar_length * progress // 100)
            bar = ":large_green_square:" * filled_length + ":white_square:" * (bar_length - filled_length)
            return f"[{bar}] {progress}%"

        def format_username(user: User) -> str:
            slack_id = getattr(user, "slack_user_id", None)
            username = getattr(user, "username", None)

            if slack_id:
                return f"<@{slack_id}>"
            if username:
                return username
            return getattr(user, "email", str(user))

        def format_tutorial(tutorial_id: int | None) -> str:
            if tutorial_id:
                tutorial = project.tutorial
                tutorial_url = Config.ManagerDashboardUrls.tutorial_url(tutorial_id=tutorial_id)
                return f"Tutorial: <{tutorial_url}|{tutorial}>\n"
            return "Tutorial: _N/A_\n"

        def status_mapping(status_enum: ProjectStatusEnum):
            label = status_enum.label

            status_to_icon: dict[ProjectStatusEnum, str] = {
                Project.Status.PUBLISHED: ":mega:",
                Project.Status.PAUSED: ":hand:",
                Project.Status.ARCHIVED: ":archived:",
            }
            return f"{label} {status_to_icon.get(status_enum, '')}".strip()

        def project_type_mapping(project_type_enum: ProjectTypeEnum) -> str:
            label = project_type_enum.label

            type_to_icon: dict[ProjectTypeEnum, str] = {
                Project.Type.FIND: ":find:",
                Project.Type.COMPARE: ":compare:",
                Project.Type.VALIDATE: ":validate:",
                Project.Type.STREET: ":street:",
                Project.Type.COMPLETENESS: ":completeness:",
                Project.Type.VALIDATE_IMAGE: ":validate_image:",
            }

            return f"{label} {type_to_icon.get(project_type_enum, '')}".strip()

        project_url = Config.ManagerDashboardUrls.project_url(project_id=project.id)
        progress_bar = generate_progress_bar(project.progress)
        username = format_username(project.created_by)
        tutorial_text = format_tutorial(project.tutorial_id)
        status = status_mapping(project.status_enum)
        project_type = project_type_mapping(project.project_type_enum)

        section_block: dict = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"Project Name: <{project_url}|{project.generate_name()}>\n"
                    f"{tutorial_text}"
                    f"Project Type: {project_type}\n"
                    f"Requesting Organization: {project.requesting_organization.name}\n"
                    f"Status: {status}\n"
                    f"Created by: {username}\n"
                    f"Created at: {project.created_at.strftime('%b. %d, %Y, %-I:%M %p')}\n\n"
                    f"{progress_bar}"
                ),
            },
        }

        if project.image:
            section_block["accessory"] = {
                "type": "image",
                "image_url": get_absolute_uri(project.image.file),
                "alt_text": "Project Cover Image",
            }

        return section_block

    @classmethod
    def get_message_for_project_progress(
        cls,
        project: Project,
    ) -> MapswipeSlack.MapswipeSlackMessageArgumentType:
        progress = project.progress
        project_url = Config.ManagerDashboardUrls.project_url(project_id=project.id)
        website_url = Config.WebsiteKeys.project(firebase_id=project.firebase_id)

        if progress >= 100:
            text = "Project reached 100%"
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Project reached 100% :tada:",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Congratulations! This project is now complete. Great work!",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"You can now _*finish*_ this <{project_url}|project> and create another one :mapswipe:",
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Visit Website",
                            "emoji": True,
                        },
                        "value": "website-link",
                        "url": website_url,
                        "action_id": "button-action",
                    },
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
                        "text": "Project reached 90% :rocket:",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Almost there! Get your next projects ready",
                    },
                },
            ]
            return {
                "text": text,
                "blocks": blocks,
            }
        text = "Project Progress"
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Project Progress!",
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
        project: Project,
    ) -> MapswipeSlack.MapswipeSlackMessageArgumentType:
        header_text = f"{project.generate_name()} :lock:" if project.is_private else project.generate_name()
        website_url = Config.WebsiteKeys.project(firebase_id=project.firebase_id)
        text = "Project Creation Successful"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": header_text,
                },
            },
            {"type": "divider"},
            SlackMessage.project_info_block(
                project,
            ),
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Happy Swiping! :slightly_smiling_face: :mapswipe:",
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Visit Website",
                        "emoji": True,
                    },
                    "value": "website-link",
                    "url": website_url,
                    "action_id": "button-action",
                },
            },
        ]

        return {
            "text": text,
            "blocks": blocks,
        }

    @classmethod
    def get_message_for_status_update(
        cls,
        project: Project,
    ) -> MapswipeSlack.MapswipeSlackMessageArgumentType:
        modified_user_slack_id = project.modified_by.slack_user_id
        modified_at = project.modified_at
        status = project.status_enum
        status_label = project.status_enum.label.lower()

        text = "Project status updated"

        if status == Project.Status.PUBLISHED:
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Project published :raised_hands:",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"This project was published by <@{modified_user_slack_id}> at {modified_at.strftime('%b. %d, %Y, %-I:%M %p')}",  # noqa: E501
                    },
                },
            ]
            return {
                "text": text,
                "blocks": blocks,
            }

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Project status update :pushpin:",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"The project was {status_label} by <@{modified_user_slack_id}> at {project.modified_at.strftime('%b. %d, %Y, %-I:%M %p')}",  # noqa: E501
                },
            },
        ]
        return {
            "text": text,
            "blocks": blocks,
        }


def base_slack_message(project_id: int, mapslack: MapswipeSlack):
    project = Project.objects.get(pk=project_id)
    message = SlackMessage.get_message_for_project_creation(project)
    slack_response = mapslack.send_slack_message(**message)
    project.slack_thread_ts = slack_response.get("ts")
    project.save(update_fields=("slack_thread_ts",))
    return project.slack_thread_ts


def check_slack_thread(project_id: int, mapslack: MapswipeSlack) -> str:
    project = Project.objects.get(pk=project_id)
    if project.slack_thread_ts:
        return project.slack_thread_ts

    return base_slack_message(project_id=project_id, mapslack=mapslack)


def update_base_message(client: MapswipeSlack, project: Project, ts: str):
    update_message = SlackMessage.get_message_for_project_creation(
        project,
    )
    client.update_slack_message(ts=ts, **update_message)

import datetime

from apps.common.models import FirebasePushStatusEnum
from apps.common.utils import get_absolute_uri
from apps.project.models import Project, ProjectStatusEnum, ProjectTypeEnum
from apps.tutorial.models import Tutorial
from apps.user.models import User
from main.config import Config
from utils.slack import MapswipeSlack

GREEN_BLK = ":large_green_square:"
WHITE_BLK = ":white_square:"


class SlackMessage:
    @staticmethod
    def format_progress_bar(progress: int, bar_length: int = 10) -> str:
        filled_length = bar_length * progress // 100
        green_bar = GREEN_BLK * filled_length
        white_bar = WHITE_BLK * (bar_length - filled_length)
        return f"{green_bar}{white_bar} {progress}%"

    @staticmethod
    def format_user_link(user: User) -> str:
        if user.slack_user_id:
            return f"<@{user.slack_user_id}>"
        return user.username or user.display_name

    @staticmethod
    def format_project_status(status_enum: ProjectStatusEnum):
        status_to_icon: dict[ProjectStatusEnum, str] = {
            Project.Status.PUBLISHED: ":mega:",
            Project.Status.PAUSED: ":hand:",
            Project.Status.WITHDRAWN: ":package:",
        }
        # FIXME: better way to concatenate this
        return f"{status_enum.label} {status_to_icon.get(status_enum, '')}".strip()

    @staticmethod
    def format_tutorial_link(tutorial: Tutorial | None):
        if not tutorial:
            return "_n/a_"
        tutorial_url = Config.ManagerDashboardUrls.tutorial_url(tutorial_id=tutorial.pk)
        return f"<{tutorial_url}|{tutorial.name}>"

    @staticmethod
    def format_project_name(project: Project, *, show_private_indicator=False):
        if project.is_private and show_private_indicator:
            return f"{project.generate_name()} :lock:"
        return project.generate_name()

    @staticmethod
    def format_project_link(project: Project):
        project_url = Config.ManagerDashboardUrls.project_url(project_id=project.pk)
        return f"<{project_url}|{SlackMessage.format_project_name(project)}>"

    @staticmethod
    def format_project_type(project_type: ProjectTypeEnum):
        label = project_type.label
        type_to_icon: dict[ProjectTypeEnum, str] = {
            Project.Type.FIND: ":find:",
            Project.Type.COMPARE: ":compare:",
            Project.Type.VALIDATE: ":validate:",
            Project.Type.STREET: ":street:",
            Project.Type.COMPLETENESS: ":completeness:",
            Project.Type.VALIDATE_IMAGE: ":validate_image:",
            # TODO: add custom :conflation: icon in slack
            Project.Type.CONFLATION: ":construction:",
        }
        # FIXME: better way to concatenate this
        return f"{label} {type_to_icon.get(project_type, '')}".strip()

    @staticmethod
    def format_datetime(value: datetime.datetime):
        return f"<!date^{int(value.timestamp())}^{{date_short}} at {{time}}|unknown time>"

    @staticmethod
    def get_project_information_block(
        project: Project,
    ) -> dict:  # type: ignore[reportMissingTypeArgument]
        progress_bar = SlackMessage.format_progress_bar(project.progress)
        username = SlackMessage.format_user_link(project.created_by)
        tutorial_text = SlackMessage.format_tutorial_link(project.tutorial)
        status = SlackMessage.format_project_status(project.status_enum)
        project_type = SlackMessage.format_project_type(project.project_type_enum)
        created_at = SlackMessage.format_datetime(project.created_at)

        section_block: dict = {  # type: ignore[reportMissingTypeArgument]
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"Tutorial: {tutorial_text}\n"
                    f"Project Type: {project_type}\n"
                    f"Requesting Organization: {project.requesting_organization.name}\n"
                    f"Status: {status}\n"
                    f"Created by: {username}\n"
                    f"Created at: {created_at}\n\n"
                    f"{progress_bar}"
                ),
            },
        }

        if project.image:
            image_url = get_absolute_uri(project.image.file)
            section_block["accessory"] = {
                "type": "image",
                "image_url": image_url,
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
                        "text": f"Congratulations! {SlackMessage.format_project_link(project)} is now complete. Great work!",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"You can now *finish* this <{project_url}|project> and create another one.",
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Visit Website",
                        },
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
            text = "Project reached 90%"
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
                        "text": (
                            f"Almost there! {SlackMessage.format_project_link(project)} is nearing completion.\n\n"
                            "Get your next projects ready."
                        ),
                    },
                },
            ]
            return {
                "text": text,
                "blocks": blocks,
            }

        text = f"Project reached {project.progress}%"
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Project reached {project.progress}%",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": "We are getting there! One swipe at a time.",
                },
            },
        ]
        return {
            "text": text,
            "blocks": blocks,
        }

    @classmethod
    def get_message_for_project_publish(
        cls,
        project: Project,
    ) -> MapswipeSlack.MapswipeSlackMessageArgumentType:
        website_url = Config.WebsiteKeys.project(firebase_id=project.firebase_id)
        project_url = Config.ManagerDashboardUrls.project_url(project_id=project.pk)

        text = "Project published! :raised_hands:"
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": SlackMessage.format_project_name(project, show_private_indicator=True),
                },
            },
            SlackMessage.get_project_information_block(project),
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": "Happy Swiping! :slightly_smiling_face: :mapswipe:",
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Manage",
                        },
                        "url": project_url,
                        "action_id": "open-manager-dashboard-link",
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Visit Website",
                        },
                        "url": website_url,
                        "action_id": "open-website-link",
                    },
                ],
            },
        ]
        return {
            "text": text,
            "blocks": blocks,
        }

    @classmethod
    def get_message_for_project_status(
        cls,
        project: Project,
    ) -> MapswipeSlack.MapswipeSlackMessageArgumentType:
        status_label = project.status_enum.label.lower()
        username = SlackMessage.format_user_link(project.modified_by)
        modified_at = SlackMessage.format_datetime(project.modified_at)

        # FIXME(tnagorra): This should be called when the project status is:
        # published, paused, withdrawn and finished

        action_failed = project.firebase_push_status_enum == FirebasePushStatusEnum.FAILED

        match project.status_enum:
            case ProjectStatusEnum.PUBLISHED:
                status_label = "published"
            case ProjectStatusEnum.PUBLISHING_FAILED:
                status_label = "published"
                action_failed = True
            case ProjectStatusEnum.PAUSED:
                status_label = "paused"
            case ProjectStatusEnum.WITHDRAWN:
                status_label = "withdrawn"
            case ProjectStatusEnum.FINISHED:
                status_label = "finished"
            case _:
                raise Exception(f"Slack message should not be sent when project status is {project.status_enum.label}")

        text = "Project status updated!"
        if action_failed:
            text = "Project status could not be updated!"

        description = f"The project has been *{status_label}* by {username} at {modified_at}"
        if action_failed:
            description = f"The project could be *{status_label}* by {username} at {modified_at}"

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": description,
                },
            },
        ]
        return {
            "text": text,
            "blocks": blocks,
        }


def send_base_slack_message(project_id: int, mapslack: MapswipeSlack) -> str | None:
    project = Project.objects.get(pk=project_id)

    message = SlackMessage.get_message_for_project_publish(project)
    slack_thread_ts = mapslack.send_slack_message(**message)

    if slack_thread_ts:
        project.slack_thread_ts = slack_thread_ts
        project.save(update_fields=("slack_thread_ts",))

    return slack_thread_ts


def get_or_create_base_slack_message(project_id: int, mapslack: MapswipeSlack) -> str | None:
    project = Project.objects.get(pk=project_id)
    if project.slack_thread_ts:
        return project.slack_thread_ts
    return send_base_slack_message(project_id=project_id, mapslack=mapslack)


def update_base_slack_message(client: MapswipeSlack, project: Project, ts: str) -> str | None:
    update_message = SlackMessage.get_message_for_project_publish(
        project,
    )
    return client.update_slack_message(ts=ts, **update_message)

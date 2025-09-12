import typing

from django.core.management.base import BaseCommand

from apps.project.tasks import send_slack_message_for_project

CommandActionType = typing.Literal[
    "project-status-update",
    "project-progress-change",
]


class Command(BaseCommand):
    help = "Send slack messages for a given project"

    @typing.override
    def add_arguments(self, parser):
        parser.add_argument(
            "--project-id",
            type=str,
            required=True,
            help="ID of the project",
        )
        subparsers = parser.add_subparsers(dest="event", help="Events to trigger", required=True)
        subparsers.add_parser("project-status-update", help="Send message for project status change")
        subparsers.add_parser("project-progress-change", help="Send message for project progress change")

    @typing.override
    def handle(self, *args, **options):
        project_id = typing.cast("str", options["project_id"])
        project_id = int(project_id)

        event = typing.cast("CommandActionType", options["event"])
        match event:
            case "project-status-update":
                send_slack_message_for_project(project_id, "status-change")
            case "project-progress-change":
                send_slack_message_for_project(project_id, "progress-change")
            case _:
                typing.assert_never(event)

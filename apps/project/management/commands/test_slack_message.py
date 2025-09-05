import typing

from django.core.management.base import BaseCommand

from apps.project.tasks import creation_success_message, progress_change_message, status_update_message

CommandActionType = typing.Literal[
    "project-creation",
    "status-update",
    "progress-change",
]


class Command(BaseCommand):
    help = "Test sending a Slack progress message for a given project"

    @typing.override
    def add_arguments(self, parser):
        parser.add_argument(
            "--project-id",
            type=str,
            required=True,
            help="ID of the project to test",
        )
        subparsers = parser.add_subparsers(dest="event", help="Event to trigger", required=True)
        subparsers.add_parser("project-creation", help="Send message for project creation")
        subparsers.add_parser("status-update", help="Project status changed")
        subparsers.add_parser("progress-change", help="Project progress change")

    @typing.override
    def handle(self, *args, **options):
        project_id = options["project_id"]
        event = options["event"]
        match event:
            case "project-creation":
                creation_success_message(project_id=project_id)
            case "status-update":
                status_update_message(project_id=project_id)
            case "progress-change":
                progress_change_message(project_id=project_id)

            case _:
                typing.assert_never(event)

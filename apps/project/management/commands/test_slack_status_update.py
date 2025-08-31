import typing

from django.core.management.base import BaseCommand, CommandError

from apps.project.models import Project
from apps.project.tasks import project_status_update_message


class Command(BaseCommand):
    help = "Test sending a Slack progress message for a given project"

    @typing.override
    def add_arguments(self, parser):
        parser.add_argument(
            "--project_id",
            type=str,
            required=True,
            help="ID of the project to test",
        )

    @typing.override
    def handle(self, *args, **options):
        project_id = options["project_id"]

        try:
            project = Project.objects.get(id=project_id)
        except Exception as err:
            raise CommandError(f"Project with id={project_id} does not exist") from err

        slack_thread = project.slack_thread_ts

        if not slack_thread:
            raise CommandError(f"Project id={project_id} has no Slack thread. Message not sent.")

        try:
            project_status_update_message.delay(project_id=project_id)
        except Exception as err:
            raise CommandError("Failed to send slack message for status update") from err

        self.stdout.write(self.style.SUCCESS("Slack message sent successfully"))

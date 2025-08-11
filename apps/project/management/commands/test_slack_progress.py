import asyncio
import typing

from django.core.management.base import BaseCommand

from apps.project.models import Project
from apps.project.tasks import mapswipe_send_message  # import your async function


class Command(BaseCommand):
    help = "Test sending a Slack progress message for a given project"

    @typing.override
    def add_arguments(self, parser):
        parser.add_argument(
            "--client_id",
            type=str,
            required=True,
            help="ULID of the project to test",
        )

    @typing.override
    def handle(self, *args, **options):
        project_id = options["client_id"]

        try:
            project = Project.objects.select_related("requesting_organization").get(client_id=project_id)
        except Project.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Project with id={project_id} does not exist"))
            return  # Exit the command gracefully

        self.stdout.write(
            self.style.NOTICE(f"Sending Slack message for project {project.id} with progress {project.progress}"),
        )

        # Run the async Slack sending in the event loop
        asyncio.run(mapswipe_send_message(project))

        self.stdout.write(self.style.SUCCESS("Slack message sent successfully"))

import typing

from django.core.management.base import BaseCommand

from apps.project.tasks import project_creation_success_message


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

        project_creation_success_message.delay(project_id=project_id)
        self.stdout.write(self.style.SUCCESS("Slack message sent successfully"))

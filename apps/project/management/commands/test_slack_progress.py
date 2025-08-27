import typing

from django.core.management.base import BaseCommand, CommandError

from apps.project.models import Project
from apps.project.tasks import send_message_for_progress
from utils.common import get_absolute_file_url


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
        except Project.DoesNotExist as err:
            raise CommandError(f"Project with id={project_id} does not exist") from err

        project_name = project.generate_name()
        progress = project.progress
        if project.image:
            cover_image_url = get_absolute_file_url(project.image.file)
        else:
            cover_image_url = "https://pbs.twimg.com/profile_images/625633822235693056/lNGUneLX_400x400.jpg"

        send_message_for_progress.delay(project_name=project_name, progress=progress, cover_image=cover_image_url)
        self.stdout.write(self.style.SUCCESS("Slack message sent successfully"))

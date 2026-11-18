import typing

from django.core.management.base import BaseCommand, CommandParser

from apps.project.models import Project
from apps.tutorial.models import Tutorial
from main.config import Config
from project_types.store import get_project_type_handler, get_tutorial_type_handler


class Command(BaseCommand):
    help = (
        "Push the required features of the projects and tutorials that are already in firebase."
        " New pushes include them, so this is only needed after adding a new feature or for existing data."
    )

    @typing.override
    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without updating firebase.",
        )

    def _push(self, label: str, firebase_path: str, features: list[str], *, dry_run: bool) -> bool:
        ref = Config.FIREBASE_HELPER.ref(firebase_path).child("requiredFeatures")
        current = ref.get() or []
        if sorted(current) == sorted(features):
            return False
        self.stdout.write(f"{label}: {current or '-'} -> {features or '-'}")
        if not dry_run:
            # NOTE: Setting an empty list removes the key from firebase
            ref.set(features or None)
        return True

    @typing.override
    def handle(self, *args, **options):  # type: ignore[reportMissingParameterType]
        dry_run: bool = options["dry_run"]
        changed = 0

        projects = Project.objects.filter(firebase_last_pushed__isnull=False).order_by("id")
        for project in projects.iterator():
            handler = get_project_type_handler(project.project_type_enum)(project)
            features = [feature.value for feature in handler.get_required_features()]
            changed += self._push(
                f"Project {project.pk} ({project.firebase_id})",
                Config.FirebaseKeys.project(project.firebase_id),
                features,
                dry_run=dry_run,
            )

        tutorials = Tutorial.objects.filter(firebase_last_pushed__isnull=False).select_related("project").order_by("id")
        for tutorial in tutorials.iterator():
            handler = get_tutorial_type_handler(tutorial.project.project_type_enum)(tutorial)
            features = [feature.value for feature in handler.get_required_features()]
            changed += self._push(
                f"Tutorial {tutorial.pk} ({tutorial.firebase_id})",
                Config.FirebaseKeys.tutorial(tutorial.firebase_id),
                features,
                dry_run=dry_run,
            )

        suffix = " (dry run, nothing was pushed)" if dry_run else ""
        self.stdout.write(self.style.SUCCESS(f"{changed} updated{suffix}"))

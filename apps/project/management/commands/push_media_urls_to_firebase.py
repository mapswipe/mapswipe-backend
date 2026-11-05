import enum
import typing
from collections.abc import Callable

from django.core.management.base import BaseCommand
from django.db.models import QuerySet

from apps.common.models import FirebasePushStatusEnum
from apps.project.models import Project, ProjectStatusEnum
from apps.project.tasks import push_project_to_firebase
from apps.tutorial.models import Tutorial, TutorialStatusEnum
from apps.tutorial.tasks import push_tutorial_to_firebase

ACTIVE_PROJECT_STATUSES = (ProjectStatusEnum.PUBLISHED, ProjectStatusEnum.PAUSED)
PUSHABLE_TUTORIAL_STATUSES = (TutorialStatusEnum.PUBLISHED, TutorialStatusEnum.ARCHIVED)


class PushResult(enum.Enum):
    PUSHED = enum.auto()
    # Another push holds the lock
    SKIPPED = enum.auto()
    FAILED = enum.auto()


class Command(BaseCommand):
    help = (
        "Push project info and tutorials of published and paused projects to firebase again,"
        " so firebase uses the current media URLs (project image, tutorial information page images)."
        " Project tasks and groups are not pushed."
    )

    @typing.override
    def add_arguments(self, parser):  # type: ignore[reportMissingParameterType]
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List the projects and tutorials which would be pushed",
        )
        parser.add_argument(
            "--project-ids",
            type=int,
            nargs="+",
            help="Only push these projects and their tutorials",
        )

    def get_projects(self, project_ids: list[int] | None) -> QuerySet[Project]:
        # Projects without firebase_last_pushed are created (with tasks) instead of updated, so they are excluded
        qs = Project.objects.filter(
            status__in=ACTIVE_PROJECT_STATUSES,
            firebase_last_pushed__isnull=False,
        )
        if project_ids:
            qs = qs.filter(id__in=project_ids)
        return qs.order_by("id")

    def get_tutorials(self, projects: QuerySet[Project]) -> QuerySet[Tutorial]:
        return Tutorial.objects.filter(
            id__in=projects.filter(tutorial__isnull=False).values("tutorial_id"),
            status__in=PUSHABLE_TUTORIAL_STATUSES,
            firebase_last_pushed__isnull=False,
        ).order_by("id")

    def push(self, obj: Project | Tutorial, push_to_firebase: Callable[[int], bool | None]) -> PushResult:
        previous_status = obj.firebase_push_status
        # The push only runs for PENDING
        obj.update_firebase_push_status(FirebasePushStatusEnum.PENDING)
        if push_to_firebase(obj.pk) is None:
            # Restore the status unless the running push has changed it
            type(obj).objects.filter(pk=obj.pk, firebase_push_status=FirebasePushStatusEnum.PENDING).update(
                firebase_push_status=previous_status,
            )
            return PushResult.SKIPPED
        obj.refresh_from_db(fields=("firebase_push_status", "status_message"))
        if obj.firebase_push_status == FirebasePushStatusEnum.SUCCESS:
            return PushResult.PUSHED
        return PushResult.FAILED

    def report(self, label: str, obj: Project | Tutorial, result: PushResult, counts: dict[PushResult, int]):
        counts[result] += 1
        if result == PushResult.PUSHED:
            self.stdout.write(self.style.SUCCESS(f"Pushed {label}"))
        elif result == PushResult.SKIPPED:
            self.stderr.write(f"Skipped {label}: another push is running")
        else:
            self.stderr.write(f"Failed to push {label}: {obj.status_message}")

    @typing.override
    def handle(self, *args, **options):  # type: ignore[reportMissingParameterType]
        dry_run = typing.cast("bool", options["dry_run"])
        project_ids = typing.cast("list[int] | None", options["project_ids"])

        projects = self.get_projects(project_ids)
        tutorials = self.get_tutorials(projects)

        counts = dict.fromkeys(PushResult, 0)
        for tutorial in tutorials:
            label = f"Tutorial(id: {tutorial.pk}, firebase_id: {tutorial.firebase_id}) {tutorial.name}"
            if dry_run:
                self.stdout.write(f"Would push {label}")
            else:
                self.report(label, tutorial, self.push(tutorial, push_tutorial_to_firebase), counts)

        for project in projects:
            label = f"Project(id: {project.pk}, firebase_id: {project.firebase_id}) {project.topic}"
            if dry_run:
                self.stdout.write(f"Would push {label}")
            else:
                self.report(label, project, self.push(project, push_project_to_firebase), counts)

        summary = (
            f"tutorials={tutorials.count()} projects={projects.count()}"
            f" skipped={counts[PushResult.SKIPPED]} failed={counts[PushResult.FAILED]}"
        )
        self.stdout.write(f"{'Dry run: ' if dry_run else ''}{summary}")

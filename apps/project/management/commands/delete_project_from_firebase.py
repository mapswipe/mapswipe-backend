import logging
import typing

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q, QuerySet

from apps.project.models import Project, ProjectStatusEnum
from main.config import Config

logger = logging.getLogger(__name__)

FH = Config.FIREBASE_HELPER

# This command is intended only for projects that are no longer contributed to.
ELIGIBLE_STATUSES = (
    ProjectStatusEnum.FINISHED,
    ProjectStatusEnum.WITHDRAWN,
)


def get_project_firebase_nodes(project: Project) -> dict[str, str]:
    """Per-project nodes to purge from Firebase.

    Intentionally excludes the scattered ``/v2/users/{userId}/contributions/{projectId}``
    nodes and the global contribution counters: those are user-facing history read by the
    apps, and deleting them would drop users' lifetime stats and force a per-user fan-out.
    See ``docs/firebase_data_flow.md``.
    """
    return {
        # /v2/tasks/{firebase_id}/ -- largest node (task geometry)
        "tasks": Config.FirebaseKeys.project_tasks(project.firebase_id),
        # /v2/groups/{firebase_id}/
        "groups": Config.FirebaseKeys.project_groups(project.firebase_id),
        # /v2/results/{firebase_id} -- already drained to Postgres by the pull
        "results": Config.FirebaseKeys.results_project_groups(project.firebase_id),
        # /v2/groupsUsers/{firebase_id}/ -- cloud-function bookkeeping, never cleaned otherwise
        "groupsUsers": Config.FirebaseKeys.project_group_users(project.firebase_id),
        # /v2/projects/{firebase_id} -- finished/withdrawn projects are not shown to contributors
        "project": Config.FirebaseKeys.project(project.firebase_id),
    }


def delete_project_from_firebase(project: Project, *, dry_run: bool) -> None:
    nodes = get_project_firebase_nodes(project)

    for label, path in nodes.items():
        if dry_run:
            logger.info(
                "[dry-run] would delete '%s' at %s (project_id=%s, firebase_id=%s)",
                label,
                path,
                project.pk,
                project.firebase_id,
            )
            continue

        FH.ref(path).delete()
        logger.info(
            "Deleted '%s' at %s (project_id=%s, firebase_id=%s)",
            label,
            path,
            project.pk,
            project.firebase_id,
        )


class Command(BaseCommand):
    help = (
        "Delete a project's data from Firebase Realtime Database. "
        "Purges the per-project nodes (tasks, groups, results, groupsUsers, project). "
        "Leaves per-user contributions and global counters untouched. "
        "Intended to be run on FINISHED and WITHDRAWN projects."
    )

    @typing.override
    def add_arguments(self, parser):  # type: ignore[reportMissingParameterType]
        selection = parser.add_argument_group("project selection")
        selection.add_argument(
            "--project-id",
            dest="project_ids",
            nargs="+",
            type=int,
            help="One or more project database ids to delete from Firebase.",
        )
        selection.add_argument(
            "--status",
            dest="statuses",
            nargs="+",
            choices=["finished", "withdrawn"],
            help="Select all projects with the given status(es).",
        )

        parser.add_argument(
            "--allow-any-status",
            action="store_true",
            help="Bypass the finished/withdrawn-only guard (use with care).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Log what would be deleted without touching Firebase.",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Skip the confirmation prompt.",
        )

    def _select_projects(self, options) -> QuerySet[Project]:  # type: ignore[reportMissingParameterType]
        project_ids = options["project_ids"]
        statuses = options["statuses"]

        if not project_ids and not statuses:
            raise CommandError("Provide --project-id and/or --status to select projects.")

        # --project-id and --status combine as an OR: either can select a project.
        query = Q()
        if project_ids:
            query |= Q(pk__in=project_ids)
        if statuses:
            status_values = [
                ProjectStatusEnum.FINISHED if s == "finished" else ProjectStatusEnum.WITHDRAWN for s in statuses
            ]
            query |= Q(status__in=status_values)

        return Project.objects.filter(query).order_by("pk")

    @typing.override
    def handle(self, *args, **options):  # type: ignore[reportMissingParameterType]
        dry_run = options["dry_run"]
        allow_any_status = options["allow_any_status"]

        projects = list(self._select_projects(options))
        if not projects:
            self.stdout.write(self.style.WARNING("No projects matched the selection."))
            return

        # Guard: this command is meant for finished/withdrawn projects only.
        if not allow_any_status:
            ineligible = [p for p in projects if p.status_enum not in ELIGIBLE_STATUSES]
            if ineligible:
                raise CommandError(
                    "Refusing to run: the following projects are not FINISHED/WITHDRAWN: "
                    + ", ".join(f"{p.pk} ({p.status_enum.label})" for p in ineligible)
                    + ". Re-run with --allow-any-status to override.",
                )

        # Skip projects that were never pushed to Firebase.
        never_pushed = [p for p in projects if not p.firebase_id or not p.firebase_last_pushed]
        if never_pushed:
            logger.warning(
                "Skipping %s project(s) never pushed to Firebase: %s",
                len(never_pushed),
                ", ".join(str(p.pk) for p in never_pushed),
            )
        projects = [p for p in projects if p not in never_pushed]
        if not projects:
            self.stdout.write(self.style.WARNING("Nothing to delete after filtering."))
            return

        # Summarise the plan.
        self.stdout.write(f"Selected {len(projects)} project(s):")
        for p in projects:
            self.stdout.write(
                f"  - project_id={p.pk} firebase_id={p.firebase_id} status={p.status_enum.label}",
            )

        if dry_run:
            self.stdout.write(self.style.NOTICE("Dry run: no changes will be made."))
        elif not options["yes"]:
            confirm = input("Proceed with deleting these projects from Firebase? [y/N] ").strip().lower()
            if confirm not in ("y", "yes"):
                self.stdout.write(self.style.WARNING("Aborted."))
                return

        for project in projects:
            delete_project_from_firebase(project, dry_run=dry_run)

        verb = "Would delete" if dry_run else "Deleted"
        self.stdout.write(self.style.SUCCESS(f"{verb} Firebase data for {len(projects)} project(s)."))

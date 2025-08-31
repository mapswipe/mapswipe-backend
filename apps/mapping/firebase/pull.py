import logging

from apps.project.models import Project
from main.bulk_managers import BulkCreateManager
from main.config import Config
from main.logging import log_extra

from .utils import (
    FirebaseCleanup,
    results_to_temp_table,
    transfer_results_from_temp_tables,
)

logger = logging.getLogger(__name__)
FH = Config.FIREBASE_HELPER


def _transfer_results_for_project(
    *,
    bulk_create_manager: BulkCreateManager,
    firebase_cleanup: FirebaseCleanup,
    project: Project,
):
    group_results = FH.ref(Config.FirebaseKeys.results_project_groups(project.firebase_id)).get()
    assert type(group_results) is dict
    results_to_temp_table(bulk_create_manager, firebase_cleanup, project, group_results)

    # generate user_group mapping session


def pull_results_from_firebase():
    # TODO: Add a lock to prevent concurrent execution. We have lock within celery

    project_firebase_id_to_fetch = FH.ref(Config.FirebaseKeys.results_projects()).get(shallow=True)
    if not project_firebase_id_to_fetch:
        logger.info("No results to fetch from firebase")
        return

    logger.info("Fetching for projects (firebase_id): %s", project_firebase_id_to_fetch)

    project_by_firebase_id = {
        project.firebase_id: project
        for project in Project.objects.filter(
            firebase_id__in=project_firebase_id_to_fetch,
        )
    }

    firebase_cleanup = FirebaseCleanup()
    bulk_create_manager = BulkCreateManager()
    for project_firebase_id in project_firebase_id_to_fetch:
        # NOTE: This check is not needed as we already have a mapping of project that does not include tutorial
        if "tutorial" in project_firebase_id:
            logger.error(
                "Tutorial should not be included in the results. It will not be transferred",
                extra=log_extra(
                    {
                        "tutorial_firebase_id": project_firebase_id,
                    },
                ),
            )
            firebase_cleanup.add_project(project_firebase_id=project_firebase_id)
            continue

        project = project_by_firebase_id.get(project_firebase_id)

        if not project:
            logger.error(
                "Project is not in DB. This will not be transferred",
                extra=log_extra(
                    {
                        "project_firebase_id": project_firebase_id,
                    },
                ),
            )
            firebase_cleanup.add_project(project_firebase_id=project_firebase_id)
            continue

        _transfer_results_for_project(
            project=project,
            firebase_cleanup=firebase_cleanup,
            bulk_create_manager=bulk_create_manager,
        )

    bulk_create_manager.done()

    transfer_results_from_temp_tables(firebase_cleanup)
    firebase_cleanup.done()

    # TODO: Trigger slack notification workflow

import logging
import shutil
from pathlib import Path

from django.core.files import File
from django.db import transaction
from ulid import ULID

from apps.common.models import AssetTypeEnum, FirebasePushStatusEnum
from apps.project.custom_options import get_custom_options
from apps.project.exports.geojson import gzipped_csv_to_gzipped_geojson
from apps.project.exports.utils.project_progress import calculate_project_progress
from apps.project.models import Project, ProjectAsset, ProjectAssetExportTypeEnum, ProjectProgressStatusEnum
from apps.project.tasks import push_project_to_firebase, send_slack_message_for_project
from apps.user.models import User
from main.config import Config
from main.logging import log_extra
from project_types.store import get_project_type_handler
from project_types.tile_map_service.compare.project import CompareProjectProperty
from project_types.tile_map_service.completeness.project import CompletenessProjectProperty
from project_types.tile_map_service.find.project import FindProjectProperty
from utils.geo.raster_tile_server.config import RasterTileServerNameEnum

from .mapping_results import generate_mapping_results
from .mapping_results_aggregate.task import generate_mapping_results_aggregate_by_task
from .mapping_results_aggregate.user import generate_mapping_results_aggregate_by_user
from .project_stats_by_date import get_project_history
from .project_task_groups import generate_project_task_groups
from .project_tasks import generate_project_tasks
from .tasking_manager_geometries import generate_tasking_manager_geometries

logger = logging.getLogger(__name__)


def _export_project_data(project: Project, tmp_directory: Path):
    project_type_handler = get_project_type_handler(project.project_type_enum)(project)
    geometry_field = "geom"
    bot_user = User.get_bot_user()

    # legacy system path: /api/results/results_{project.id}.csv.gz
    tmp_mapping_results_csv = tmp_directory / f"results_{project.id}.csv.gz"
    # legacy system path: /api/tasks/tasks_{project.id}.csv.gz
    tmp_project_task_csv = tmp_directory / f"tasks_{project.id}.csv.gz"
    # legacy system path: /api/groups/groups_{project.id}.csv.gz
    tmp_project_task_group_csv = tmp_directory / f"groups_{project.id}.csv.gz"
    # legacy system path: /api/agg_results/agg_results_{project.id}.csv.gz
    tmp_mapping_results_aggregate_by_task_csv = tmp_directory / f"agg_results_by_task_{project.id}.csv.gz"
    # legacy system path: /api/agg_results/agg_results_{project.id}_geom.geojson.gz
    tmp_mapping_results_aggregate_by_task_geojson = (
        tmp_directory / f"agg_results_by_task_{project.id}_{geometry_field}.geojson.gz"
    )
    # legacy system path: /api/users/users_{project.id}.csv.gz
    tmp_mapping_results_aggregate_by_user_csv = tmp_directory / f"users_{project.id}.csv.gz"
    # legacy system path: /api/history/history_{project.id}.csv
    tmp_project_stats_by_date_csv = tmp_directory / f"history_{project.id}.csv"
    # legacy system path: /api/yes_maybe/yes_maybe_{project.id}.geojson
    tmp_tasking_manager_yes_maybe_geojson = tmp_directory / f"yes_maybe_{project.id}.geojson"
    # legacy system path: /api/hot_tm/hot_tm_{project.id}.geojson
    tmp_tasking_manager_hot_tm_geojson = tmp_directory / f"hot_tm_{project.id}.geojson"

    # FIXME(tnagorra): move this to project handler
    tile_servers = set[RasterTileServerNameEnum]()
    if isinstance(
        project_type_handler.project_type_specifics,
        FindProjectProperty,
    ):
        tile_servers.add(project_type_handler.project_type_specifics.tile_server_property.name)
    elif isinstance(
        project_type_handler.project_type_specifics,
        CompareProjectProperty,
    ):
        tile_servers.add(project_type_handler.project_type_specifics.tile_server_property.name)
        tile_servers.add(project_type_handler.project_type_specifics.tile_server_b_property.name)
    elif isinstance(
        project_type_handler.project_type_specifics,
        CompletenessProjectProperty,
    ):
        tile_servers.add(project_type_handler.project_type_specifics.tile_server_property.name)
        if project_type_handler.project_type_specifics.overlay_tile_server_property.raster:
            tile_servers.add(
                project_type_handler.project_type_specifics.overlay_tile_server_property.raster.tile_server.name,
            )

    add_metadata = (
        RasterTileServerNameEnum.MAXAR_STANDARD in tile_servers or RasterTileServerNameEnum.MAXAR_PREMIUM in tile_servers
    )

    custom_options_raw = []

    # NOTE: We do not have custom options for Compare, Completeness and Find projects
    if not isinstance(
        project_type_handler.project_type_specifics,
        # NOTE: Using negate test to throw type error if new project type is added
        (CompareProjectProperty | CompletenessProjectProperty | FindProjectProperty),
    ):
        custom_options_raw = [
            {"value": custom_option.value}
            for custom_option in project_type_handler.project_type_specifics.custom_options or []
        ]

    # Fallback if custom options is not defined
    if not custom_options_raw:
        custom_options_raw = get_custom_options(project.project_type_enum)

    # TODO: Cache tasks and groups as they don't change (if cached, make sure to remove Unnamed column)
    tasks_df = generate_project_tasks(destination_filename=tmp_project_task_csv, project=project)
    groups_df = generate_project_task_groups(destination_filename=tmp_project_task_group_csv, project=project)

    results_df = generate_mapping_results(destination_filename=tmp_mapping_results_csv, project=project)

    aggregate_results_by_task_df = generate_mapping_results_aggregate_by_task(
        destination_filename=tmp_mapping_results_aggregate_by_task_csv,
        results_df=results_df,
        tasks_df=tasks_df,
        custom_options_raw=custom_options_raw,
        project=project,
    )

    gzipped_csv_to_gzipped_geojson(
        gzip_csv_source_filename=tmp_mapping_results_aggregate_by_task_csv,
        destination_filename=tmp_mapping_results_aggregate_by_task_geojson,
        add_metadata=add_metadata,
        geometry_field=geometry_field,
    )

    # Aggregated users by users
    aggregate_results_by_user_df = None
    try:
        aggregate_results_by_user_df = generate_mapping_results_aggregate_by_user(
            results_df=results_df,
            agg_results_df=aggregate_results_by_task_df,
            project=project,
        )

        aggregate_results_by_user_df.to_csv(
            tmp_mapping_results_aggregate_by_user_csv,
            index_label="idx",
        )

        logger.info(
            "saved agg results by user id for %s: %s",
            project.id,
            tmp_mapping_results_aggregate_by_user_csv.name,
        )
    except MemoryError:
        logger.error(
            "failed to agg results by user id",
            extra=log_extra({"project_id": project.id}),
            exc_info=True,
        )

    project_stats_by_date_df = get_project_history(
        results_df=results_df,
        groups_df=groups_df,
        project=project,
        destination_filename=tmp_project_stats_by_date_csv,
    )
    logger.info(
        "saved project stats by date for %s: %s",
        project.id,
        tmp_project_stats_by_date_csv.name,
    )

    if project_type_handler.generate_hot_tm_geometries():
        generate_tasking_manager_geometries(
            project=project,
            agg_results_filename=tmp_mapping_results_aggregate_by_task_csv,
            yes_maybe_destination_filename=tmp_tasking_manager_yes_maybe_geojson,
            hot_tm_destination_filename=tmp_tasking_manager_hot_tm_geojson,
        )

    if not project_stats_by_date_df.empty:
        project.number_of_contributor_users = project_stats_by_date_df["cum_number_of_users"].iloc[-1]
        project.number_of_results = project_stats_by_date_df["cum_number_of_results"].iloc[-1]
        project.number_of_results_for_progress = project_stats_by_date_df["cum_number_of_results_progress"].iloc[-1]
        project.last_contribution_date = project_stats_by_date_df.index[-1]

        previous_progress = project.progress
        project.progress = calculate_project_progress(project)

        if project.progress >= 100:
            project.progress_status = ProjectProgressStatusEnum.COMPLETED

        if project.progress >= 90 and (project.slack_progress_notifications or 0) < 90:
            transaction.on_commit(
                lambda: send_slack_message_for_project.delay(project_id=project.id, action="progress-change"),
            )

        if project.progress >= 100 and (project.slack_progress_notifications or 0) < 100:
            transaction.on_commit(
                lambda: send_slack_message_for_project.delay(project_id=project.id, action="progress-change"),
            )

        if project.progress != previous_progress:
            transaction.on_commit(
                lambda: push_project_to_firebase.delay(project_id=project.id, only_stats=True),
            )
            project.update_firebase_push_status(FirebasePushStatusEnum.PENDING, False)

    project.save(
        update_fields=(
            "progress",
            "progress_status",
            "number_of_contributor_users",
            "number_of_results",
            "number_of_results_for_progress",
            "last_contribution_date",
            "firebase_push_status",
            "firebase_last_pushed",
        ),
    )

    for export_type, file in [
        (ProjectAssetExportTypeEnum.AGGREGATED_RESULTS, tmp_mapping_results_aggregate_by_task_csv),
        (ProjectAssetExportTypeEnum.AGGREGATED_RESULTS_WITH_GEOMETRY, tmp_mapping_results_aggregate_by_task_geojson),
        (ProjectAssetExportTypeEnum.RESULTS, tmp_mapping_results_csv),
        (ProjectAssetExportTypeEnum.TASKS, tmp_project_task_csv),
        (ProjectAssetExportTypeEnum.GROUPS, tmp_project_task_group_csv),
        (ProjectAssetExportTypeEnum.USERS, tmp_mapping_results_aggregate_by_user_csv),
        (ProjectAssetExportTypeEnum.HISTORY, tmp_project_stats_by_date_csv),
        (
            ProjectAssetExportTypeEnum.MODERATE_TO_HIGH_AGREEMENT_YES_MAYBE_GEOMETRIES,
            tmp_tasking_manager_yes_maybe_geojson,
        ),
        (ProjectAssetExportTypeEnum.HOT_TASKING_MANAGER_GEOMETRIES, tmp_tasking_manager_hot_tm_geojson),
    ]:
        if not file.is_file():
            continue

        with Path.open(file, "rb") as fp:
            django_file = File(fp, name=file.name)
            django_file_size = django_file.size
            fp.seek(0)

            project_asset, _ = ProjectAsset.objects.update_or_create(
                project=project,
                type=AssetTypeEnum.EXPORT,
                export_type=export_type,
                create_defaults=dict(
                    client_id=str(ULID()),  # NOTE: This shouldn't change
                    created_by=bot_user,
                    modified_by=bot_user,
                    mimetype=ProjectAssetExportTypeEnum.get_mimetype(export_type),
                    file=django_file,
                    file_size=django_file_size,
                ),
                # the following values are used for update
                defaults=dict(
                    mimetype=ProjectAssetExportTypeEnum.get_mimetype(export_type),
                    modified_by=bot_user,
                    file=django_file,
                    file_size=django_file_size,
                ),
            )

            logger.info("Saved export file %s to %s", project_asset.type_enum.label, project_asset.file)


def export_project_data(project: Project):
    if project.old_id and project.old_id not in [
        # XXX: whitelist for prod project's active during migration
        # TODO: Remove this whitelist
        "-OZFXKuj8LuLnBeE3lay",  # Validate - Sragen East - Indonesia (1) American Red Cross
        "-OUoQBZkwX2q2t_Sx0uI",  # STREET - Waste Mapping - Dar es Salaam, Tanzania (3) HeiGIT
    ]:
        logger.error(
            "Project export called for old project.. Not running",
            extra=log_extra(
                {
                    "project_id": project.id,
                    "project_old_id": project.old_id,
                },
            ),
        )
        return

    new_temp_directory = Config.TEMP_DIR / str(ULID())
    new_temp_directory.mkdir(parents=True)
    try:
        _export_project_data(project, new_temp_directory)
    except Exception:
        logger.error(
            "Unexpected error occurred during project export",
            extra=log_extra(dict(project=project.id)),
            exc_info=True,
        )
    # Local temporary files cleanup
    if new_temp_directory.exists() and new_temp_directory.is_dir():
        shutil.rmtree(new_temp_directory)

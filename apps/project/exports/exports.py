import logging
import shutil
from pathlib import Path

from django.core.files import File
from ulid import ULID

from apps.common.models import AssetTypeEnum
from apps.project.exports.geojson import gzipped_csv_to_gzipped_geojson
from apps.project.models import Project, ProjectAsset, ProjectAssetExportTypeEnum, ProjectTypeEnum
from apps.user.models import User
from main.config import Config
from main.logging import log_extra
from project_types.store import get_project_type_handler
from project_types.tile_map_service.compare.project import CompareProjectProperty
from project_types.tile_map_service.completeness.project import CompletenessProjectProperty
from project_types.tile_map_service.find.project import FindProjectProperty

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

    # TODO: if maxar is used for tile_server_name, this should be true
    add_metadata = False

    custom_options_raw = []
    if not isinstance(
        project_type_handler.project_type_specifics,
        (
            # NOTE: Using negate test to throw type error if new project type is added
            # TODO: Or we should just use project.project_type_specifics.get("custom_options", [])?
            CompareProjectProperty | CompletenessProjectProperty | FindProjectProperty
        ),
    ):
        custom_options_raw = [
            {"value": custom_option.value}
            for custom_option in project_type_handler.project_type_specifics.custom_options or []
        ]

    # Fallback: TODO: Is this okay?
    custom_options_raw = custom_options_raw or [
        {"value": 0},
        {"value": 1},
        {"value": 2},
    ]

    # TODO: Cache tasks and groups as they don't change (if cached, make sure to remove Unnamed column)
    tasks_df = generate_project_tasks(destination_filename=tmp_project_task_csv, project=project)
    groups_df = generate_project_task_groups(destination_filename=tmp_project_task_group_csv, project=project)

    results_df = generate_mapping_results(destination_filename=tmp_mapping_results_csv, project=project)

    aggregate_results_by_task_df = generate_mapping_results_aggregate_by_task(
        destination_filename=tmp_mapping_results_aggregate_by_task_csv,
        results_df=results_df,
        tasks_df=tasks_df,
        custom_options_raw=custom_options_raw,
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
        logger.error("failed to agg results by user id", extra=log_extra({"project_id": project.id}))

    get_project_history(
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

    generate_hot_tm_geometries = project.project_type in [
        ProjectTypeEnum.COMPARE,
        ProjectTypeEnum.COMPLETENESS,
        ProjectTypeEnum.FIND,
    ]

    if generate_hot_tm_geometries:
        generate_tasking_manager_geometries(
            project=project,
            agg_results_filename=tmp_mapping_results_aggregate_by_task_csv,
            yes_maybe_destination_filename=tmp_tasking_manager_yes_maybe_geojson,
            hot_tm_destination_filename=tmp_tasking_manager_hot_tm_geojson,
        )

    # TODO: is this required? from existing system
    # create_project_stats_dict

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
        # AREA_OF_INTEREST,
    ]:
        if not file.is_file():
            continue

        with Path.open(file, "rb") as fp:
            django_file = File(fp, name=file.name)

            project_asset, _ = ProjectAsset.objects.update_or_create(
                project=project,
                type=AssetTypeEnum.EXPORT,
                export_type=export_type,
                create_defaults=dict(
                    client_id=str(ULID()),  # NOTE: This shouldn't change
                    created_by=bot_user,
                    modified_by=bot_user,
                    mimetype=ProjectAssetExportTypeEnum.get_meme_type(export_type),
                    file=django_file,
                    file_size=django_file.size,
                ),
                defaults=dict(
                    mimetype=ProjectAssetExportTypeEnum.get_meme_type(export_type),
                    modified_by=bot_user,
                    file=django_file,
                    file_size=django_file.size,
                ),
            )

            logger.info("Saved export file %s to %s", project_asset.type, project_asset.file)


def export_project_data(project: Project):
    new_temp_directory = Config.TEMP_DIR / str(ULID())
    new_temp_directory.mkdir(parents=True)
    try:
        _export_project_data(project, new_temp_directory)
    except Exception:
        logger.error("Unexpected error occurred during project export", extra=log_extra(dict(project=project.id)))
    # Local temporary files cleanup
    if new_temp_directory.exists() and new_temp_directory.is_dir():
        shutil.rmtree(new_temp_directory)

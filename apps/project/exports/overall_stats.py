import csv
import io
import logging
import subprocess
import tempfile
import typing
from pathlib import Path

from django.contrib.gis.db.models.functions import AsWKT
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.fields.files import FieldFile

from apps.common.models import GlobalExportAsset, GlobalExportAssetTypeEnum
from apps.common.utils import get_absolute_uri
from apps.project.models import Project, ProjectAsset, ProjectStatusEnum, ProjectTypeEnum
from main.config import Config
from utils.common import get_random_string

logger = logging.getLogger(__name__)


class ManualField: ...


MANUAL_FIELD = ManualField()


def _project_queryset(
    fieldnames: typing.Mapping[str, typing.Any],
    queryset: models.QuerySet[Project, dict[str, typing.Any] | Project] | None = None,
):
    base_queryset = queryset or Project.objects
    return base_queryset.annotate(
        **{fieldname: query_ for fieldname, query_ in fieldnames.items() if query_ not in [MANUAL_FIELD, None]},
    ).values(
        *[fieldname for fieldname, query_ in fieldnames.items() if query_ is not MANUAL_FIELD],
    )


def regenerate_project_stats_by_types_csv():
    logger.info("Processing regenerate_project_stats_by_types_csv")
    fieldnames = {
        "project_type": None,
        "project_type_display": MANUAL_FIELD,
        "projects_count": models.Count("*"),
        "total_area_sqkm": models.Sum("total_area"),
        "total_number_of_results": models.Count("number_of_results"),
        "total_number_of_results_progress": models.Count("number_of_results_for_progress"),
        "average_number_of_users_per_project": models.Avg("number_of_contributor_users"),
    }

    projects_aggregate_qs = _project_queryset(fieldnames, queryset=Project.objects.values("project_type"))

    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    for data in projects_aggregate_qs:
        data["project_type_display"] = ProjectTypeEnum(data["project_type"]).label
        writer.writerow(data)

    csv_content = ContentFile(
        csv_buffer.getvalue().encode("utf-8"),
        name=GlobalExportAssetTypeEnum.get_file_name(GlobalExportAssetTypeEnum.PROJECT_STATS_BY_TYPES),
    )

    GlobalExportAsset.objects.update_or_create(
        type=GlobalExportAssetTypeEnum.PROJECT_STATS_BY_TYPES,
        defaults={
            "file": csv_content,
            "file_size": csv_content.size,
        },
    )
    logger.info("Processed regenerate_project_stats_by_types_csv")


def regenerate_projects_csv(temp_projects_csv: typing.IO):  # type: ignore[reportMissingTypeArgument]
    logger.info("Processing regenerate_projects_csv")

    fieldnames = {
        "id": None,
        "firebase_id": None,
        "name": Project.generate_name_query(),
        "description": None,
        "look_for": None,
        "project_type": None,
        "project_type_display": MANUAL_FIELD,
        "organization_name": models.F("requesting_organization__name"),
        "image_url": models.F("image__file"),
        "created_at": None,
        # TODO: "custom_options": None,
        # TODO: "tile_server_names": None,
        "status": None,
        "status_display": MANUAL_FIELD,
        "area_sqkm": models.F("aoi_geometry__total_area"),
        # TODO: Change _centroid to centroid after `centroid` field is removed from the project's table
        "centroid": MANUAL_FIELD,
        "_centroid": AsWKT("aoi_geometry__centroid"),
        "geom": AsWKT("aoi_geometry__geometry"),
        "progress": None,  # NOTE: This is changed to float later
        "number_of_contributor_users": None,
        "number_of_results": None,
        "number_of_results_for_progress": None,
        "last_contribution_date": None,
    }

    projects_aggregate_qs = _project_queryset(fieldnames)

    fieldnames.pop("_centroid")

    writer = csv.DictWriter(temp_projects_csv, fieldnames=fieldnames)
    writer.writeheader()

    for data in projects_aggregate_qs:
        image_file = data["image_url"]
        image_file_url = get_absolute_uri(
            # XXX: Temporary file field
            FieldFile(
                instance=None,  # pyright: ignore[reportArgumentType]
                field=ProjectAsset.file.field,
                name=image_file,
            ),
        )
        # TODO: Remove this logic to set centroid after `centroid` field is removed from the project's table
        data["centroid"] = data.pop("_centroid")
        data["image_url"] = image_file_url
        data["status_display"] = ProjectStatusEnum(data["status"]).label
        data["project_type_display"] = ProjectTypeEnum(data["project_type"]).label
        data["progress"] = data["progress"] / 100

        writer.writerow(data)

    temp_projects_csv.seek(0)
    csv_file = ContentFile(temp_projects_csv.read().encode("utf-8"))
    csv_file.name = GlobalExportAssetTypeEnum.get_file_name(GlobalExportAssetTypeEnum.PROJECTS_CSV)

    GlobalExportAsset.objects.update_or_create(
        type=GlobalExportAssetTypeEnum.PROJECTS_CSV,
        defaults={
            "file": csv_file,
            "file_size": csv_file.size,
        },
    )
    logger.info("Processed regenerate_projects_csv")


def _regenerate_projects_centroid_for_geometry_field(
    projects_csv_inputfile: Path,
    geometry_field: str,
    asset_type: GlobalExportAssetTypeEnum,
):
    logger.info("Processing regenerate_projects_centroid_geojson")

    tmp_geojson_outfile = Config.TEMP_DIR / f"projects_centroid_{geometry_field}_{get_random_string(6)}.geojson"
    inputfile_without_path = projects_csv_inputfile.name.split("/")[-1].replace(".csv", "")

    # TODO: Use EXCLUDE after upgrading gdal to > 3.9.0 https://github.com/OSGeo/gdal/pull/8675
    # With that, we can use `SELECT * EXCLUDE(geom), CAST(...` to exclude one column
    with Path.open(projects_csv_inputfile, "r") as fp:
        csv_reader = csv.DictReader(fp)
        inputfile_columns = [column for column in csv_reader.fieldnames or [] if column != "geom"]
        inputfile_columns_str = ",".join(inputfile_columns)

    subprocess.run(  # noqa: S603
        [
            "/usr/bin/ogr2ogr",
            "-nln",
            "projects",
            "-f",
            "GeoJSON",
            str(tmp_geojson_outfile),
            str(projects_csv_inputfile),
            "-sql",
            f'SELECT {inputfile_columns_str}, CAST({geometry_field} as geometry) FROM "{inputfile_without_path}"',
        ],
        check=True,
    )

    with Path.open(tmp_geojson_outfile, "rb") as fp:
        geojson_file = ContentFile(fp.read())
        geojson_file.name = GlobalExportAssetTypeEnum.get_file_name(asset_type)

        GlobalExportAsset.objects.update_or_create(
            type=asset_type,
            defaults={
                "file": geojson_file,
                "file_size": geojson_file.size,
            },
        )

    tmp_geojson_outfile.unlink()
    logger.info("Processed regenerate_projects_centroid_geojson")


def regenerate_projects_centroid_geojson(projects_csv_inputfile: Path):
    _regenerate_projects_centroid_for_geometry_field(
        projects_csv_inputfile,
        "centroid",
        GlobalExportAssetTypeEnum.PROJECTS_CENTROID_GEOJSON,
    )


def regenerate_projects_geom_geojson(projects_csv_inputfile: Path):
    _regenerate_projects_centroid_for_geometry_field(
        projects_csv_inputfile,
        "geom",
        GlobalExportAssetTypeEnum.PROJECTS_GEOM_GEOJSON,
    )


def generate():
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".csv", dir=Config.TEMP_DIR) as temp_projects_csv:
        regenerate_projects_csv(temp_projects_csv)
        regenerate_projects_centroid_geojson(Path(temp_projects_csv.name))
        regenerate_projects_geom_geojson(Path(temp_projects_csv.name))
    regenerate_project_stats_by_types_csv()

"""Object source tests of Validate projects.

Each test checks the inputs of one object source type, stores the AOI it covers as the project's
AOI geometry asset, and records its inputs on the project as the last passed test.
"""

import dataclasses
import json
import typing

import pydantic
from django.contrib.gis.geos import GEOSGeometry
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from ulid import ULID

from apps.common.models import AssetMimetypeEnum, AssetTypeEnum
from apps.project.models import Project, ProjectAsset, ProjectAssetInputTypeEnum, ProjectTypeEnum
from apps.user.models import User
from project_types.base.project import ValidationException
from project_types.tile_map_service.base.project import create_json_dump
from project_types.validate.project import (
    ValidateObjectSourceConfig,
    ValidateObjectSourceTestRecord,
    ValidateObjectSourceTypeEnum,
    ValidateProject,
)
from utils import fields as custom_fields
from utils.asset_types.models import AoiGeometryAssetProperty
from utils.geo.transform import convert_json_dict_to_geometry_collection, get_area_of_geometry

TESTABLE_PROJECT_STATUSES = (
    Project.Status.DRAFT,
    Project.Status.PROCESSING_FAILED,
)


@dataclasses.dataclass
class ObjectSourceTestResult:
    object_count: int
    aoi_geometry_asset: ProjectAsset


def get_testable_project(project_id: int | str) -> Project:
    project = Project.objects.filter(pk=project_id).first()
    if project is None:
        raise ValidationException("Project does not exist")
    if project.project_type_enum != ProjectTypeEnum.VALIDATE:
        raise ValidationException("Object source tests are only available for Validate projects")
    if project.status_enum not in TESTABLE_PROJECT_STATUSES:
        raise ValidationException(f"Cannot test the object source of a project with status {project.status_enum.label}")
    return project


def _build_inputs(**kwargs: typing.Any) -> ValidateObjectSourceConfig:
    try:
        return ValidateObjectSourceConfig(**kwargs)
    except pydantic.ValidationError as e:
        messages = "; ".join(str(error["msg"]) for error in e.errors())
        raise ValidationException(f"Invalid object source: {messages}") from e


def _create_aoi_geometry_asset(
    project: Project,
    user: User,
    aoi_geojson: dict[str, typing.Any],
    geometry: GEOSGeometry,
    filename: str,
) -> ProjectAsset:
    file = ContentFile(create_json_dump(aoi_geojson), filename)
    centroid = geometry.centroid
    asset_type_specifics = AoiGeometryAssetProperty(
        bbox=geometry.extent,
        center=(centroid.x, centroid.y),
        area=get_area_of_geometry(geometry),
    )
    return ProjectAsset.objects.create(
        client_id=str(ULID()),
        project=project,
        type=AssetTypeEnum.INPUT,
        input_type=ProjectAssetInputTypeEnum.AOI_GEOMETRY,
        mimetype=AssetMimetypeEnum.GEOJSON,
        file=file,
        file_size=file.size,
        asset_type_specifics=asset_type_specifics.model_dump(mode="json"),
        created_by=user,
        modified_by=user,
    )


def _record_passed_test(
    project: Project,
    user: User,
    inputs: ValidateObjectSourceConfig,
    aoi_geometry_asset: ProjectAsset,
    object_count: int,
) -> ObjectSourceTestResult:
    previous_test = (
        ValidateObjectSourceTestRecord.model_validate(project.last_passed_object_source_test)
        if project.last_passed_object_source_test
        else None
    )

    # NOTE: Assets created by an earlier Tasking Manager or Object GeoJSON URL test are not used anymore.
    # An uploaded AOI file belongs to the project manager, so we keep it.
    if (
        previous_test is not None
        and previous_test.inputs.source_type != ValidateObjectSourceTypeEnum.AOI_GEOJSON_FILE
        and int(previous_test.aoi_geometry_asset) != aoi_geometry_asset.pk
    ):
        ProjectAsset.objects.filter(
            pk=int(previous_test.aoi_geometry_asset),
            project=project,
            type=AssetTypeEnum.INPUT,
            input_type=ProjectAssetInputTypeEnum.AOI_GEOMETRY,
        ).update(marked_as_deleted=True)

    record = ValidateObjectSourceTestRecord(
        inputs=inputs.get_test_inputs(),
        aoi_geometry_asset=str(aoi_geometry_asset.pk),
        object_count=object_count,
        tested_at=timezone.now(),
    )
    project.last_passed_object_source_test = record.model_dump(mode="json", exclude_none=True)
    project.aoi_geometry_input_asset = aoi_geometry_asset
    project.modified_by = user
    project.save(
        update_fields=(
            "last_passed_object_source_test",
            "aoi_geometry_input_asset",
            "modified_by",
            "modified_at",
        ),
    )

    return ObjectSourceTestResult(
        object_count=object_count,
        aoi_geometry_asset=aoi_geometry_asset,
    )


def run_aoi_geojson_file_test(
    project: Project,
    user: User,
    asset_id: int | str,
    ohsome_filter: str,
) -> ObjectSourceTestResult:
    inputs = _build_inputs(
        source_type=ValidateObjectSourceTypeEnum.AOI_GEOJSON_FILE,
        aoi_geometry=str(asset_id),
        ohsome_filter=ohsome_filter,
    )
    aoi_asset = (
        ProjectAsset.usable_objects()
        .filter(
            id=asset_id,
            type=ProjectAsset.Type.INPUT,
            input_type=ProjectAssetInputTypeEnum.AOI_GEOMETRY,
            project_id=project.pk,
        )
        .first()
    )

    object_count, _ = ValidateProject.test_ohsome_objects_from_aoi_asset(aoi_asset, ohsome_filter)
    assert aoi_asset is not None

    with transaction.atomic():
        return _record_passed_test(project, user, inputs, aoi_asset, object_count)


def run_tasking_manager_test(
    project: Project,
    user: User,
    hot_tm_id: custom_fields.PydanticId,
    ohsome_filter: str,
) -> ObjectSourceTestResult:
    inputs = _build_inputs(
        source_type=ValidateObjectSourceTypeEnum.TASKING_MANAGER,
        tasking_manager_project_id=hot_tm_id,
        ohsome_filter=ohsome_filter,
    )
    object_count, aoi_geojson, _ = ValidateProject.test_tasking_manager_project(hot_tm_id, ohsome_filter)
    # NOTE: The test already made sure that this is a valid feature collection
    _, geometry_collection = convert_json_dict_to_geometry_collection(aoi_geojson)

    with transaction.atomic():
        aoi_asset = _create_aoi_geometry_asset(
            project,
            user,
            aoi_geojson,
            geometry_collection,
            f"tasking_manager_{hot_tm_id}_aoi.geojson",
        )
        return _record_passed_test(project, user, inputs, aoi_asset, object_count)


def run_object_geojson_url_test(
    project: Project,
    user: User,
    url: str,
) -> ObjectSourceTestResult:
    inputs = _build_inputs(
        source_type=ValidateObjectSourceTypeEnum.OBJECT_GEOJSON_URL,
        object_geojson_url=url,
    )
    assert inputs.object_geojson_url is not None
    url = inputs.object_geojson_url
    object_count, _, geometry_collection = ValidateProject.test_geojson_url_project(url)

    hull = geometry_collection.convex_hull
    aoi_geojson = {
        "type": "FeatureCollection",
        "metadata": {
            "object_geojson_url": url,
        },
        "features": [
            {
                "type": "Feature",
                "geometry": json.loads(hull.geojson),
                "properties": {
                    "object_geojson_url": url,
                },
            },
        ],
    }

    with transaction.atomic():
        aoi_asset = _create_aoi_geometry_asset(
            project,
            user,
            aoi_geojson,
            hull,
            "object_geojson_url_aoi.geojson",
        )
        return _record_passed_test(project, user, inputs, aoi_asset, object_count)

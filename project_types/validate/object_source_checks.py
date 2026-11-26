"""Object source tests of Tasking Manager and Object GeoJSON URL Validate projects.

Each test checks the inputs of one object source type and stores the AOI it covers as an AOI geometry
asset of the project, marked as deleted. The test does not change the project: the dashboard sends the
asset in object_source.aoi_geometry when the project is saved, which attaches it and clears the mark.

AOI GeoJSON file projects are tested with the testAoiObjects query instead, which stores nothing,
as the uploaded AOI file is already a project asset.
"""

import dataclasses
import json
import typing

import pydantic
from django.contrib.gis.geos import GEOSGeometry
from django.core.files.base import ContentFile
from ulid import ULID

from apps.common.models import AssetMimetypeEnum, AssetTypeEnum
from apps.project.models import Project, ProjectAsset, ProjectAssetInputTypeEnum, ProjectTypeEnum
from apps.user.models import User
from project_types.base.project import ValidationException
from project_types.tile_map_service.base.project import create_json_dump
from project_types.validate.project import (
    ValidateObjectSourceConfig,
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


def get_testable_project(project_id: int) -> Project:
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
        # NOTE: Marked as deleted means no saved project uses this asset yet. Saving the project clears it.
        marked_as_deleted=True,
        created_by=user,
        modified_by=user,
    )


def run_tasking_manager_test(
    project: Project,
    user: User,
    hot_tm_id: custom_fields.PydanticId,
    ohsome_filter: str,
) -> ObjectSourceTestResult:
    _build_inputs(
        source_type=ValidateObjectSourceTypeEnum.TASKING_MANAGER,
        tasking_manager_project_id=hot_tm_id,
        ohsome_filter=ohsome_filter,
    )
    object_count, aoi_geojson, _ = ValidateProject.test_tasking_manager_project(hot_tm_id, ohsome_filter)
    # NOTE: The test already made sure that this is a valid feature collection
    _, geometry_collection = convert_json_dict_to_geometry_collection(aoi_geojson)

    aoi_asset = _create_aoi_geometry_asset(
        project,
        user,
        aoi_geojson,
        geometry_collection,
        f"tasking_manager_{hot_tm_id}_aoi.geojson",
    )
    return ObjectSourceTestResult(object_count=object_count, aoi_geometry_asset=aoi_asset)


def run_object_geojson_url_test(
    project: Project,
    user: User,
    url: str,
) -> ObjectSourceTestResult:
    inputs = _build_inputs(
        source_type=ValidateObjectSourceTypeEnum.OBJECT_GEOJSON_URL,
        object_geojson_url=url,
    )
    # NOTE: The validated URL is the URL as given, without surrounding whitespace
    assert inputs.object_geojson_url is not None
    url = inputs.object_geojson_url
    object_count, _, geometry_collection = ValidateProject.test_geojson_url_project(url)

    hull = geometry_collection.convex_hull
    # NOTE: The hull is the project area, so it has the same limit as the AOI of the other source types
    ValidateProject.validate_geojson_aoi_area(get_area_of_geometry(hull))
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

    aoi_asset = _create_aoi_geometry_asset(
        project,
        user,
        aoi_geojson,
        hull,
        "object_geojson_url_aoi.geojson",
    )
    return ObjectSourceTestResult(object_count=object_count, aoi_geometry_asset=aoi_asset)

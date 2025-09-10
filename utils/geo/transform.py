import json
from typing import Any
from warnings import deprecated

from django.contrib.gis.geos import GeometryCollection, GEOSGeometry
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from geojson_pydantic import Feature as PydanticFeature
from geojson_pydantic import FeatureCollection as PydanticFeatureCollection
from geojson_pydantic.geometries import MultiPolygon as PydanticMultiPolygon
from geojson_pydantic.geometries import Polygon as PydanticPolygon
from osgeo import ogr


def convert_json_str_to_wkt(geometry: str):
    # FIXME: Use gis.geos.GEOSGeometry instead of ogr
    geom = ogr.CreateGeometryFromJson(geometry)
    if geom.GetCoordinateDimension() == 3:
        geom.FlattenTo2D()
    return geom.ExportToWkt()


def convert_feature_to_wkt(feature: PydanticFeature[PydanticPolygon | PydanticMultiPolygon, dict[str, Any]]):
    if feature.geometry is None:
        return None
    return convert_json_str_to_wkt(feature.geometry.model_dump_json())


@deprecated("We can directly use geojson_pydantic with more specific geometry")
def validate_geojson_file(file: ContentFile) -> None:
    """Validates if the given file contains a valid GeoJSON FeatureCollection.

    Args:
        file: File object

    Raises:
        ValidationError: If the file is not a valid JSON or does not conform to GeoJSON standards.
        ValueError: If the GeoJSON doesn't meet expected structure.

    """
    try:
        geojson_data = json.load(file)
    except json.JSONDecodeError as e:
        raise ValidationError("Invalid JSON format in the file.") from e

    feature_collection = PydanticFeatureCollection.model_validate(geojson_data)

    if not feature_collection.features:
        raise ValidationError("GeoJSON 'features' list cannot be empty.")


def convert_json_dict_to_geometry_collection(geojson_dict: dict):
    AoiGeometryFeature = PydanticFeature[PydanticPolygon | PydanticMultiPolygon, dict]
    AoiGeometryFeatureCollection = PydanticFeatureCollection[AoiGeometryFeature]

    feature_collection = AoiGeometryFeatureCollection.model_validate(geojson_dict)

    geometries: list[GEOSGeometry] = []
    for feature in feature_collection.features:
        if not feature.geometry:
            continue
        geometry = GEOSGeometry(feature.geometry.model_dump_json(), srid=4326)
        geometries.append(geometry)

    geometry_collection = GeometryCollection(geometries)
    geometry_collection.srid = 4326
    return geometry_collection

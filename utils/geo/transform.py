import json
from typing import Any
from warnings import deprecated

from django.contrib.gis.geos import GeometryCollection, GEOSGeometry, Polygon
from django.contrib.gis.geos.prototypes.io import wkt_w
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from geojson_pydantic import Feature as PydanticFeature
from geojson_pydantic import FeatureCollection as PydanticFeatureCollection
from geojson_pydantic.geometries import MultiPolygon as PydanticMultiPolygon
from geojson_pydantic.geometries import Polygon as PydanticPolygon
from osgeo import ogr  # type: ignore[reportMissingTypeStubs]


# FIXME(tnagorra): Is there are more performant way to do this?
def to_2d(geom: GEOSGeometry) -> GEOSGeometry:
    wkt_writer = wkt_w(dim=2)
    wkt_2d = wkt_writer.write(geom).decode()
    return GEOSGeometry(wkt_2d, srid=geom.srid)


def get_area_of_geometry(geom: GeometryCollection | GEOSGeometry):
    area_m2: float = geom.transform(6933, clone=True).area
    return area_m2 / 1_000_000


def get_polygon_of_extent(extent: tuple[float, float, float, float]):
    min_lng, min_lat, max_lng, max_lat = extent
    return Polygon(
        (
            (min_lng, min_lat),
            (min_lng, max_lat),
            (max_lng, max_lat),
            (max_lng, min_lat),
            (min_lng, min_lat),
        ),
    )


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
def validate_geojson_file(file: ContentFile) -> None:  # type: ignore[reportMissingTypeArgument]
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


AoiFeature = PydanticFeature[PydanticPolygon | PydanticMultiPolygon, dict[str, Any]]


def convert_json_dict_to_features(geojson_dict: dict):  # type: ignore[reportMissingTypeArgument]
    feature_collection = PydanticFeatureCollection.model_validate(geojson_dict)

    polygon_types = (PydanticPolygon, PydanticMultiPolygon)
    filtered_features: list[AoiFeature] = [
        feature for feature in feature_collection.features if isinstance(feature.geometry, polygon_types)
    ]
    return filtered_features


def convert_json_dict_to_geometry_collection(geojson_dict: dict):  # type: ignore[reportMissingTypeArgument]
    filtered_features = convert_json_dict_to_features(geojson_dict)

    geometries: list[GEOSGeometry] = []
    for feature in filtered_features:
        if not feature.geometry:
            continue
        geometry = GEOSGeometry(feature.geometry.model_dump_json(), srid=4326)
        geometries.append(to_2d(geometry))

    geometry_collection = GeometryCollection(geometries)
    geometry_collection.srid = 4326

    return filtered_features, geometry_collection

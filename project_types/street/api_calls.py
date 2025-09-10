import logging
from collections.abc import Hashable
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from typing import Any
from warnings import deprecated

import mercantile
import pandas as pd
import requests
from geojson_pydantic import FeatureCollection as PydanticFeatureCollection
from geojson_pydantic.geometries import MultiPolygon as PydanticMultiPolygon
from geojson_pydantic.geometries import Polygon as PydanticPolygon
from pydantic import ValidationError
from shapely import MultiPolygon as ShapelyMultiPolygon
from shapely import Point as ShapelyPoint
from shapely import Polygon as ShapelyPolygon
from shapely import box, unary_union
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry as ShapelyBaseGeometry
from vt2geojson import tools as vt2geojson_tools

from main.config import Config
from main.logging import log_extra_response
from project_types.base.project import ValidationException
from utils.common import Grouping
from utils.spatial_sampling import spatial_sampling

logger = logging.getLogger(__name__)


class StreetFeature(ShapelyPoint): ...


class StreetException(Exception):
    pass


def create_tiles(
    *,
    polygon: ShapelyBaseGeometry,
    level: int,
) -> pd.DataFrame:
    if not isinstance(polygon, ShapelyPolygon | ShapelyMultiPolygon):
        return pd.DataFrame(columns=pd.Index(["x", "y", "z", "geometry"]))

    if isinstance(polygon, ShapelyPolygon):
        polygon = ShapelyMultiPolygon([polygon])

    tiles: set[mercantile.Tile] = set()
    for _, poly in enumerate(polygon.geoms):
        tiles.update(list(mercantile.tiles(*poly.bounds, level)))

    bbox_polygons = [
        box(
            *mercantile.bounds(
                tile.x,
                tile.y,
                tile.z,
            ),
        )
        for tile in tiles
    ]
    return pd.DataFrame(
        {
            "x": [tile.x for tile in tiles],
            "y": [tile.y for tile in tiles],
            "z": [tile.z for tile in tiles],
            "geometry": bbox_polygons,
        },
    )


def geojson_to_polygon(geojson_data: dict[str, Any]):
    # NOTE: We might not need this, as we already check this
    try:
        fc = PydanticFeatureCollection(**geojson_data)
    except ValidationError as e:
        raise ValidationException("Invalid GeoJSON FeatureCollection") from e

    polygon_types = (PydanticPolygon, PydanticMultiPolygon)
    geometries = [shape(feature.geometry) for feature in fc.features if isinstance(feature.geometry, polygon_types)]

    if not geometries:
        raise ValidationException("No valid Polygon or MultiPolygon found in the GeoJSON FeatureCollection")

    return unary_union(geometries)


def coordinate_download(
    *,
    polygon: ShapelyBaseGeometry,
    level: int,
    kwargs: dict[str, Any],
) -> pd.DataFrame:
    tiles = create_tiles(
        polygon=polygon,
        level=level,
    )

    if tiles.empty:
        return pd.DataFrame()

    downloaded_metadata: list[pd.DataFrame] = []
    for row in tiles.to_dict(orient="records"):
        df = download_and_process_tile(
            row=row,
            polygon=polygon,
            kwargs=kwargs,
        )
        if df is not None and not df.empty:
            downloaded_metadata.append(df)

    if downloaded_metadata:
        return pd.concat(downloaded_metadata, ignore_index=True)

    return pd.DataFrame()


@deprecated("This function is deprecated and will be removed in future versions.")
def parallelized_processing(
    data: list[pd.DataFrame],
    kwargs: dict[str, Any],
    polygon: ShapelyBaseGeometry,
    tiles: pd.DataFrame,
    workers: int,
):
    process_tile_with_args = partial(download_and_process_tile, polygon=polygon, kwargs=kwargs)

    with ProcessPoolExecutor(max_workers=workers) as executor:
        tile_dicts = tiles.to_dict(orient="records")
        futures = list(executor.map(process_tile_with_args, tile_dicts))

        for df in futures:
            if df is not None and not df.empty:
                data.append(df)
    return data


def download_and_process_tile(
    *,
    row: dict[Hashable, Any],
    polygon: ShapelyBaseGeometry,
    kwargs: dict[str, Any],
    attempt_limit: int = 3,
) -> pd.DataFrame | None:
    z = row["z"]
    x = row["x"]
    y = row["y"]
    z, x, y = row["z"], row["x"], row["y"]
    url = f"{Config.MAPILLARY_API_LINK}{z}/{x}/{y}?access_token={Config.MAPILLARY_API_KEY}"

    attempt = 0
    while attempt < attempt_limit:
        try:
            data = get_mapillary_data(url, x, y, z)
            if data.isna().all() is False or data.empty is False:
                data = data[data["geometry"].apply(lambda point: point.within(polygon))]
                target_columns = [
                    "id",
                    "geometry",
                    "captured_at",
                    "is_pano",
                    "compass_angle",
                    "sequence",
                    "organization_id",
                ]
                for col in target_columns:
                    if col not in data.columns:
                        data[col] = None
                if data.isna().all() is False or data.empty is False:
                    data = filter_results(data, **kwargs)
                return data
        except StreetException:
            logger.warning(
                "Error while fetching Mapillary data for tile %s/%s/%s",
                z,
                x,
                y,
            )
            attempt += 1
    return None


def get_mapillary_data(
    url: str,
    x: int,
    y: int,
    z: int,
) -> pd.DataFrame:
    response = requests.get(url, timeout=100)
    if response.status_code != 200:
        logger.warning(
            "Mapillary API request failed",
            extra=log_extra_response(response=response),
        )
        raise StreetException

    features = vt2geojson_tools.vt_bytes_to_geojson(response.content, x, y, z).get(
        "features",
        [],
    )
    data: list[dict[str, Any]] = []
    data.extend(
        [
            {
                "geometry": ShapelyPoint(feature["geometry"]["coordinates"]),
                **feature.get("properties", {}),
            }
            for feature in features
            if feature.get("geometry", {}).get("type") == "Point"
        ],
    )
    return pd.DataFrame(data)


def filter_results(
    results_df: pd.DataFrame,
    creator_id: int | None = None,
    is_pano: bool | None = None,
    organization_id: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
):
    df = results_df.copy()
    if creator_id is not None:
        if df["creator_id"].isna().all():
            logger.info("No Mapillary Feature in the AoI has a 'creator_id' value.")
            return None
        df = df[df["creator_id"] == creator_id]

    if is_pano is not None:
        if df["is_pano"].isna().all():
            logger.info("No Mapillary Feature in the AoI has a 'is_pano' value.")
            return None
        df = df[df["is_pano"] == is_pano]

    if organization_id is not None:
        if df["organization_id"].isna().all():
            logger.info(
                "No Mapillary Feature in the AoI has an 'organization_id' value.",
            )
            return None
        df = df[df["organization_id"] == organization_id]

    if start_time is not None:
        if df["captured_at"].isna().all():
            logger.info("No Mapillary Feature in the AoI has a 'captured_at' value.")
            return None
        df = filter_by_timerange(df, start_time, end_time)

    return df


def filter_by_timerange(df: pd.DataFrame, start_time: str, end_time: str | None = None) -> pd.DataFrame:
    df["captured_at"] = pd.to_datetime(df["captured_at"], unit="ms")
    converted_start_time = pd.to_datetime(start_time).tz_localize(None)
    converted_end_time = pd.to_datetime(end_time).tz_localize(None) if end_time else pd.Timestamp.now().tz_localize(None)
    return df[(df["captured_at"] >= converted_start_time) & (df["captured_at"] <= converted_end_time)]


def get_image_metadata(
    *,
    aoi_geojson: dict[str, Any],
    level: int = 14,
    is_pano: bool | None = False,
    creator_id: str | None = None,
    organization_id: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    randomize_order: bool = False,
    sampling_threshold: int | None = None,
) -> Grouping[StreetFeature]:
    kwargs = {
        "is_pano": is_pano,
        "creator_id": creator_id,
        "organization_id": organization_id,
        "start_time": start_time,
        "end_time": end_time,
    }
    aoi_polygon = geojson_to_polygon(aoi_geojson)
    downloaded_metadata = coordinate_download(
        polygon=aoi_polygon,
        level=level,
        kwargs=kwargs,
    )
    if downloaded_metadata.empty or downloaded_metadata.isna().all() is True:
        raise ValidationException(
            "No Mapillary features found in the area of interest with the provided filters.",
        )
    if sampling_threshold is not None:
        downloaded_metadata = spatial_sampling(
            df=downloaded_metadata,
            interval_length=sampling_threshold,
        )

    if randomize_order is True:
        downloaded_metadata = downloaded_metadata.sample(frac=1).reset_index(drop=True)

    downloaded_metadata = downloaded_metadata.drop_duplicates(subset=["geometry"])

    total_images = len(downloaded_metadata)
    if total_images > 100000:
        raise ValidationException(
            f"Too many Images with selected filter options for the AoI: {total_images}",
        )

    return Grouping[StreetFeature](
        feature_ids=downloaded_metadata["id"].tolist(),
        features=downloaded_metadata["geometry"].tolist(),
    )

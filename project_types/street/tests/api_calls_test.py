import json
import typing
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from shapely import wkt
from shapely.geometry import GeometryCollection, MultiPolygon, Point, Polygon

from main.config import Config
from project_types.base.project import ValidationException
from project_types.street.api_calls import (
    coordinate_download,
    create_tiles,
    download_and_process_tile,
    filter_by_timerange,
    filter_results,
    geojson_to_polygon,
    get_image_metadata,
)
from utils.geo.street_image_provider.models import StreetImageProvider, StreetImageProviderNameEnum

if typing.TYPE_CHECKING:
    from collections.abc import Hashable


class TestTileGroupingFunctions(unittest.TestCase):
    level: int  # type: ignore[reportUninitializedInstanceVariable]
    test_polygon: Polygon  # type: ignore[reportUninitializedInstanceVariable]
    empty_polygon: Polygon  # type: ignore[reportUninitializedInstanceVariable]
    empty_geometry: GeometryCollection  # type: ignore[reportUninitializedInstanceVariable]
    row: pd.Series  # type: ignore[reportUninitializedInstanceVariable]
    provider: StreetImageProvider  # type: ignore[reportUninitializedInstanceVariable]

    @typing.override
    @classmethod
    def setUpClass(cls):
        with Path(Config.BASE_DIR, "assets/fixtures/street_aoi.geojson").open(encoding="utf-8") as file:
            cls.fixture_data = json.load(file)

        with Path(Config.BASE_DIR, "assets/fixtures/mapillary_response.csv").open(encoding="utf-8") as file:
            df = pd.read_csv(file)
            df["geometry"] = df["geometry"].apply(wkt.loads)  # type: ignore[reportArgumentType]
            cls.fixture_df = df

    @typing.override
    def setUp(self):
        self.level = 14
        self.test_polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        self.empty_polygon = Polygon()
        self.empty_geometry = GeometryCollection()
        self.row = pd.Series({"x": 1, "y": 1, "z": self.level})
        self.provider = StreetImageProvider(
            name=StreetImageProviderNameEnum.MAPILLARY,
            url=Config.MAPILLARY_API_LINK,
        )

    def test_create_tiles_with_valid_polygon(self):
        tiles = create_tiles(polygon=self.test_polygon, level=self.level)
        assert not tiles.empty

    def test_create_tiles_with_multipolygon(self):
        polygon = Polygon(
            [
                (0.00000000, 0.00000000),
                (0.000000001, 0.00000000),
                (0.00000000, 0.000000001),
                (0.00000000, 0.000000001),
            ],
        )
        multipolygon = MultiPolygon([polygon, polygon])
        tiles = create_tiles(polygon=multipolygon, level=self.level)
        assert not tiles.empty
        assert len(tiles) == 1

    def test_create_tiles_with_empty_polygon(self):
        tiles = create_tiles(polygon=self.empty_polygon, level=self.level)
        assert tiles.empty

    def test_create_tiles_with_empty_geometry(self):
        tiles = create_tiles(polygon=self.empty_geometry, level=self.level)
        assert tiles.empty

    def test_geojson_to_polygon_feature_collection_with_multiple_polygons(self):
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]],
                    },
                    "properties": {},
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[(2, 2), (3, 2), (3, 3), (2, 3), (2, 2)]],
                    },
                    "properties": {},
                },
            ],
        }
        result = geojson_to_polygon(geojson_data)
        assert isinstance(result, MultiPolygon)
        assert len(result.geoms) == 2

    def test_geojson_to_polygon_single_feature_polygon(self):
        geojson_data = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]],
            },
            "properties": {},
        }
        result = geojson_to_polygon(geojson_data)
        assert isinstance(result, Polygon)

    def test_geojson_to_polygon_single_feature_multipolygon(self):
        geojson_data = {
            "type": "Feature",
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [
                    [[(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]],
                    [[(2, 2), (3, 2), (3, 3), (2, 3), (2, 2)]],
                ],
            },
            "properties": {},
        }
        result = geojson_to_polygon(geojson_data)
        assert isinstance(result, MultiPolygon)
        assert len(result.geoms) == 2

    def test_geojson_to_polygon_non_polygon_geometry_in_feature_collection(self):
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": [(0, 0), (1, 1)]},
                    "properties": {},
                },
            ],
        }
        with pytest.raises(ValidationException) as context:
            geojson_to_polygon(geojson_data)
        assert str(context.value) == "Non-polygon geometries cannot be combined into a MultiPolygon."

    def test_geojson_to_polygon_empty_feature_collection(self):
        geojson_data = {"type": "FeatureCollection", "features": []}
        result = geojson_to_polygon(geojson_data)
        assert result.is_empty

    def test_geojson_to_polygon_contribution_geojson(self):
        result = geojson_to_polygon(self.fixture_data)
        assert isinstance(result, Polygon)

    @patch("project_types.street.api_calls.vt2geojson_tools.vt_bytes_to_geojson")
    @patch("project_types.street.api_calls.requests.get")
    def test_download_and_process_tile_success(self, mock_get, mock_vt2geojson):  # type: ignore[reportMissingParameterType]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"mock vector tile data"  # Example mock data
        mock_get.return_value = mock_response

        mock_vt2geojson.return_value = {
            "features": [
                {
                    "geometry": {"type": "Point", "coordinates": [0, 0]},
                    "properties": {"id": 1},
                },
            ],
        }

        row: dict[Hashable, typing.Any] = {"x": 1, "y": 1, "z": 14}

        polygon = wkt.loads("POLYGON ((-1 -1, -1 1, 1 1, 1 -1, -1 -1))")

        result = download_and_process_tile(row=row, polygon=polygon, kwargs={}, provider=self.provider)
        assert result is not None
        assert len(result) == 1
        assert result["geometry"][0].wkt == "POINT (0 0)"

    @patch("project_types.street.api_calls.requests.get")
    def test_download_and_process_tile_failure(self, mock_get):  # type: ignore[reportMissingParameterType]
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = download_and_process_tile(row=self.row, polygon=self.test_polygon, kwargs={}, provider=self.provider)
        assert result is None

    @patch("project_types.street.api_calls.get_street_image_data")
    def test_download_and_process_tile_spatial_filtering(self, mock_get_street_image_data):  # type: ignore[reportMissingParameterType]
        inside_points = [
            (0.2, 0.2),
            (0.5, 0.5),
        ]
        outside_points = [
            (1.5, 0.5),
            (0.5, 1.5),
            (-0.5, 0.5),
        ]
        points = inside_points + outside_points
        data = [
            {
                "geometry": Point(x, y),
            }
            for x, y in points
        ]

        mock_get_street_image_data.return_value = pd.DataFrame(data)

        metadata = download_and_process_tile(row=self.row, polygon=self.test_polygon, kwargs={}, provider=self.provider)
        assert metadata is not None
        metadata = metadata.drop_duplicates()
        assert len(metadata) == len(inside_points)

    @patch("project_types.street.api_calls.download_and_process_tile")
    def test_coordinate_download_with_failures(self, mock_download_and_process_tile):  # type: ignore[reportMissingParameterType]
        mock_download_and_process_tile.return_value = pd.DataFrame()

        metadata = coordinate_download(polygon=self.test_polygon, level=self.level, kwargs={}, provider=self.provider)

        assert metadata.empty

    def test_filter_within_time_range(self):
        start_time = "2016-01-20 00:00:00"
        end_time = "2022-01-21 23:59:59"
        filtered_df = filter_by_timerange(self.fixture_df, start_time, end_time)

        assert len(filtered_df) == 3
        assert all(filtered_df["captured_at"] >= pd.to_datetime(start_time))
        assert all(filtered_df["captured_at"] <= pd.to_datetime(end_time))

    def test_filter_without_end_time(self):
        start_time = "2020-01-20 00:00:00"
        filtered_df = filter_by_timerange(self.fixture_df, start_time)

        assert len(filtered_df) == 3
        assert all(filtered_df["captured_at"] >= pd.to_datetime(start_time))

    def test_filter_time_no_data(self):
        start_time = "2016-01-30 00:00:00"
        end_time = "2016-01-31 00:00:00"
        filtered_df = filter_by_timerange(self.fixture_df, start_time, end_time)
        assert filtered_df.empty

    def test_filter_default(self):
        filtered_df = filter_results(self.fixture_df)
        assert filtered_df is not None
        assert len(filtered_df) == len(self.fixture_df)

    def test_filter_pano_true(self):
        filtered_df = filter_results(self.fixture_df, is_pano=True)
        assert filtered_df is not None
        assert len(filtered_df) == 3

    def test_filter_pano_false(self):
        filtered_df = filter_results(self.fixture_df, is_pano=False)
        assert filtered_df is not None
        assert len(filtered_df) == 3

    def test_filter_organization_id(self):
        filtered_df = filter_results(self.fixture_df, organization_id=1)
        assert filtered_df is not None
        assert len(filtered_df) == 1

    def test_filter_creator_id(self):
        filtered_df = filter_results(self.fixture_df, creator_id=102506575322825)
        assert filtered_df is not None
        assert len(filtered_df) == 3

    def test_filter_time_range(self):
        start_time = "2016-01-20 00:00:00"
        end_time = "2022-01-21 23:59:59"
        filtered_df = filter_results(
            self.fixture_df,
            start_time=start_time,
            end_time=end_time,
        )
        assert filtered_df is not None
        assert len(filtered_df) == 3

    def test_filter_no_rows_after_filter(self):
        filtered_df = filter_results(self.fixture_df, is_pano="False")  # type: ignore[reportArgumentType]
        assert filtered_df is not None
        assert filtered_df.empty

    def test_filter_missing_columns(self):
        columns_to_check = [
            "is_pano",
            "organization_id",
            "captured_at",
        ]
        for column in columns_to_check:
            df_copy = self.fixture_df.copy()
            df_copy[column] = None

            if column == "captured_at":
                column = "start_time"  # noqa: PLW2901

            result = filter_results(df_copy, **{column: True})  # type: ignore[reportArgumentType]
            assert result is None

    @patch("project_types.street.api_calls.coordinate_download")
    def test_get_image_metadata(self, mock_coordinate_download):  # type: ignore[reportMissingParameterType]
        mock_coordinate_download.return_value = self.fixture_df
        result = get_image_metadata(aoi_geojson=self.fixture_data)
        assert isinstance(result, dict)
        assert "feature_ids" in result
        assert "features" in result

    @patch("project_types.street.api_calls.coordinate_download")
    def test_get_image_metadata_empty_response(self, mock_coordinate_download):  # type: ignore[reportMissingParameterType]
        df = self.fixture_df.copy()
        df = df.drop(df.index)
        mock_coordinate_download.return_value = df

        with pytest.raises(ValidationException):
            get_image_metadata(aoi_geojson=self.fixture_data)

    @patch("project_types.street.api_calls.filter_results")
    @patch("project_types.street.api_calls.coordinate_download")
    def test_get_image_metadata_size_restriction(
        self,
        mock_coordinate_download,  # type: ignore[reportMissingParameterType]
        mock_filter_results,  # type: ignore[reportMissingParameterType]
    ):
        mock_df = pd.DataFrame({"id": range(1, 100002), "geometry": range(1, 100002)})
        mock_coordinate_download.return_value = mock_df
        with pytest.raises(ValidationException):
            get_image_metadata(aoi_geojson=self.fixture_data)

    @patch("project_types.street.api_calls.coordinate_download")
    def test_get_image_metadata_drop_duplicates(self, mock_coordinate_download):  # type: ignore[reportMissingParameterType]
        test_df = pd.DataFrame(
            {
                "id": [1, 2, 2, 3, 4, 4, 5],
                "geometry": ["a", "b", "b", "c", "d", "d", "e"],
            },
        )
        mock_coordinate_download.return_value = test_df
        return_dict = get_image_metadata(aoi_geojson=self.fixture_data)

        return_df = pd.DataFrame(return_dict)

        assert len(return_df) != len(test_df)

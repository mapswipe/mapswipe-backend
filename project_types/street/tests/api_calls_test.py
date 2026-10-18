import json
import re
import traceback
import typing
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests
from pydantic import ValidationError
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
from utils.geo.street_image_provider.models import (
    StreetImageProviderConfig,
    StreetImageProviderEnum,
    StreetImageProviderNormConfig,
)

if typing.TYPE_CHECKING:
    from collections.abc import Hashable


def get_provider_config(provider: StreetImageProviderEnum, **config: typing.Any) -> StreetImageProviderNormConfig:
    return StreetImageProviderConfig.model_validate({"provider": provider, provider.value: config}).get_config()


class TestTileGroupingFunctions(unittest.TestCase):
    level: int  # type: ignore[reportUninitializedInstanceVariable]
    test_polygon: Polygon  # type: ignore[reportUninitializedInstanceVariable]
    empty_polygon: Polygon  # type: ignore[reportUninitializedInstanceVariable]
    empty_geometry: GeometryCollection  # type: ignore[reportUninitializedInstanceVariable]
    row: pd.Series  # type: ignore[reportUninitializedInstanceVariable]
    provider: StreetImageProviderNormConfig  # type: ignore[reportUninitializedInstanceVariable]

    @typing.override
    @classmethod
    def setUpClass(cls):
        with Path(Config.BASE_DIR, "assets/fixtures/street_aoi.geojson").open(encoding="utf-8") as file:
            cls.fixture_data = json.load(file)

        with Path(Config.BASE_DIR, "assets/fixtures/mapillary_response.csv").open(encoding="utf-8") as file:
            df = pd.read_csv(file)
            df["geometry"] = df["geometry"].apply(wkt.loads)  # type: ignore[reportArgumentType]
            df["captured_at"] = pd.to_datetime(df["captured_at"], unit="ms")
            cls.fixture_df = df

    @typing.override
    def setUp(self):
        self.level = 14
        self.test_polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        self.empty_polygon = Polygon()
        self.empty_geometry = GeometryCollection()
        self.row = pd.Series({"x": 1, "y": 1, "z": self.level})
        self.provider = get_provider_config(StreetImageProviderEnum.MAPILLARY)

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

    @patch("project_types.street.api_calls.get_street_image_data")
    def test_download_and_process_tile_panoramax(self, mock_get_street_image_data):
        mock_get_street_image_data.return_value = pd.DataFrame(
            [
                {
                    "geometry": wkt.loads("POINT (0 0)"),
                    "account_id": 1,
                    "ts": "2026-02-24T10:00:00Z",
                    "type": "equirectangular",
                    "first_sequence": 42,
                },
            ],
        )

        row: dict[Hashable, typing.Any] = {"x": 1, "y": 1, "z": 14}
        polygon = wkt.loads("POLYGON ((-1 -1, -1 1, 1 1, 1 -1, -1 -1))")

        provider = get_provider_config(StreetImageProviderEnum.PANORAMAX)

        result = download_and_process_tile(
            row=row,
            polygon=polygon,
            kwargs={},
            provider=provider,
        )

        assert result is not None
        assert "creator_id" in result.columns
        assert "captured_at" in result.columns
        assert pd.api.types.is_datetime64_ns_dtype(result["captured_at"])
        assert result["captured_at"].iloc[0] == pd.to_datetime("2026-02-24T10:00:00Z").tz_localize(None)
        assert "is_pano" in result.columns
        assert result["is_pano"].iloc[0]

    @patch("project_types.street.api_calls.get_street_image_data")
    def test_download_and_process_tile_panoramax_timestamps_and_type(self, mock_get_street_image_data):
        mock_get_street_image_data.return_value = pd.DataFrame(
            [
                {"geometry": wkt.loads("POINT (0 0)"), "id": "a", "ts": "2025-03-29 10:00:00+01"},
                {"geometry": wkt.loads("POINT (0 0)"), "id": "b", "ts": "2025-03-31 10:00:00+02"},
            ],
        )
        result = download_and_process_tile(
            row={"x": 1, "y": 1, "z": 15},
            polygon=wkt.loads("POLYGON ((-1 -1, -1 1, 1 1, 1 -1, -1 -1))"),
            kwargs={},
            provider=get_provider_config(StreetImageProviderEnum.PANORAMAX),
        )
        assert result is not None
        assert list(result["captured_at"].astype(str)) == ["2025-03-29 09:00:00", "2025-03-31 08:00:00"]
        assert not result["is_pano"].any()

    @patch("project_types.street.api_calls.get_street_image_data")
    def test_download_and_process_tile_returns_none(self, mock_get_street_image_data):
        mock_get_street_image_data.return_value = pd.DataFrame()

        row: dict[Hashable, typing.Any] = {"x": 1, "y": 1, "z": 14}
        polygon = wkt.loads("POLYGON ((-1 -1, -1 1, 1 1, 1 -1, -1 -1))")

        result = download_and_process_tile(
            row=row,
            polygon=polygon,
            provider=self.provider,
            kwargs={},
        )

        assert result is None

    @patch("project_types.street.api_calls.requests.get")
    def test_download_and_process_tile_failure(self, mock_get):  # type: ignore[reportMissingParameterType]
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = download_and_process_tile(row=self.row, polygon=self.test_polygon, kwargs={}, provider=self.provider)
        assert result is None

    @patch("project_types.street.api_calls.get_street_image_data")
    def test_download_and_process_tile_panoramax_custom_url(self, mock_get_street_image_data):  # type: ignore[reportMissingParameterType]
        mock_get_street_image_data.return_value = pd.DataFrame()
        cases = [
            ("https://panoramax.example.com", "https://panoramax.example.com/api/map/14/1/1.mvt"),
            ("https://panoramax.example.com/", "https://panoramax.example.com/api/map/14/1/1.mvt"),
            ("https://panoramax.example.com:8443", "https://panoramax.example.com:8443/api/map/14/1/1.mvt"),
            ("https://panoramax.example.com:8443/", "https://panoramax.example.com:8443/api/map/14/1/1.mvt"),
            ("http://localhost:8080", "http://localhost:8080/api/map/14/1/1.mvt"),
            ("http://192.168.1.2", "http://192.168.1.2/api/map/14/1/1.mvt"),
        ]
        for url, expected_tile_url in cases:
            mock_get_street_image_data.reset_mock()
            provider = get_provider_config(StreetImageProviderEnum.PANORAMAX_CUSTOM, url=url)

            download_and_process_tile(row=self.row, polygon=self.test_polygon, kwargs={}, provider=provider)

            mock_get_street_image_data.assert_called_once_with(expected_tile_url, 1, 1, 14, params={})

    @patch.object(Config, "MAPILLARY_API_KEY", "secret-token")
    @patch("project_types.street.api_calls.requests.get")
    def test_download_and_process_tile_failure_does_not_log_access_token(self, mock_get):  # type: ignore[reportMissingParameterType]
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.url = f"{Config.MAPILLARY_API_LINK}14/1/1?access_token=secret-token"
        mock_response.content = b""
        mock_get.return_value = mock_response

        with self.assertLogs("project_types.street.api_calls", level="WARNING") as logs:
            download_and_process_tile(row=self.row, polygon=self.test_polygon, kwargs={}, provider=self.provider)

        assert mock_get.call_args.kwargs["params"] == {"access_token": "secret-token"}
        for record in logs.records:
            assert "secret-token" not in record.getMessage()

    @patch.object(Config, "MAPILLARY_API_KEY", "secret-token")
    @patch("project_types.street.api_calls.requests.get")
    def test_download_and_process_tile_request_errors(self, mock_get):  # type: ignore[reportMissingParameterType]
        request_errors = [
            requests.exceptions.ConnectionError("Max retries exceeded with url: /14/1/1?access_token=secret-token"),
            requests.exceptions.ReadTimeout("Read timed out: /14/1/1?access_token=secret-token"),
            requests.exceptions.InvalidURL("Invalid URL: /14/1/1?access_token=secret-token"),
            requests.exceptions.TooManyRedirects("Exceeded redirects: /14/1/1?access_token=secret-token"),
            requests.exceptions.ChunkedEncodingError("Connection broken: /14/1/1?access_token=secret-token"),
        ]
        for request_error in request_errors:
            mock_get.reset_mock()
            mock_get.side_effect = request_error
            with pytest.raises(ValidationException) as context:
                download_and_process_tile(row=self.row, polygon=self.test_polygon, kwargs={}, provider=self.provider)

            mock_get.assert_called_once()
            # NOTE: The formatted traceback is what `exc_info=True` writes to the logs
            formatted_error = "".join(traceback.format_exception(context.value))
            assert "/14/1/1" in formatted_error
            assert "secret-token" not in formatted_error

    @patch.object(Config, "MAPILLARY_API_KEY", "secret-token")
    @patch("project_types.street.api_calls.requests.get")
    def test_download_and_process_tile_invalid_vector_tile(self, mock_get):  # type: ignore[reportMissingParameterType]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<html><body>Not a vector tile</body></html>"
        mock_get.return_value = mock_response

        with pytest.raises(ValidationException, match="valid vector tile") as context:
            download_and_process_tile(row=self.row, polygon=self.test_polygon, kwargs={}, provider=self.provider)

        mock_get.assert_called_once()
        formatted_error = "".join(traceback.format_exception(context.value))
        assert "/14/1/1" in formatted_error
        assert "secret-token" not in formatted_error

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

    @patch("project_types.street.api_calls.create_tiles")
    def test_coordinate_download_no_tiles(self, mock_create_tiles):
        mock_create_tiles.return_value = pd.DataFrame()

        metadata = coordinate_download(
            polygon=Polygon(),
            level=0,
            kwargs={},
            provider=self.provider,
        )
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
        filtered_df = filter_results(self.fixture_df, pano_only=True)
        assert filtered_df is not None
        assert len(filtered_df) == 3

    def test_filter_pano_true_with_missing_values(self):
        df = pd.DataFrame({"id": [1, 2, 3, 4], "is_pano": [True, None, False, float("nan")]})
        filtered_df = filter_results(df, pano_only=True)
        assert filtered_df is not None
        assert filtered_df["id"].tolist() == [1]

    def test_filter_pano_false(self):
        filtered_df = filter_results(self.fixture_df, pano_only=False)
        assert filtered_df is not None
        assert len(filtered_df) == len(self.fixture_df)

    def test_filter_organization_id(self):
        filtered_df = filter_results(self.fixture_df, organization_id="1")
        assert filtered_df is not None
        assert len(filtered_df) == 1

    def test_filter_creator_id(self):
        filtered_df = filter_results(self.fixture_df, creator_id="102506575322825")
        assert filtered_df is not None
        assert len(filtered_df) == 3

    def test_filter_ids_with_missing_values(self):
        df = pd.DataFrame(
            {
                "creator_id": [102506575322825, None, "a1b2c3d4-0000-4000-8000-000000000000"],
                "organization_id": [1, None, None],
            },
        )
        assert len(filter_results(df, creator_id="102506575322825")) == 1  # type: ignore[reportArgumentType]
        assert len(filter_results(df, creator_id="a1b2c3d4-0000-4000-8000-000000000000")) == 1  # type: ignore[reportArgumentType]
        assert len(filter_results(df, organization_id="1")) == 1  # type: ignore[reportArgumentType]

    def test_filter_results_no_creator_id(self):
        df = pd.DataFrame(
            {
                "creator_id": [None, None],
                "is_pano": [True, False],
                "organization_id": [1, 2],
                "captured_at": pd.to_datetime(["2026-02-24", "2026-02-25"]),
            },
        )
        filtered_df = filter_results(df, creator_id="123")
        assert filtered_df is None

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
        filtered_df = filter_results(self.fixture_df, pano_only="False")  # type: ignore[reportArgumentType]
        assert filtered_df is not None
        assert len(filtered_df) == len(self.fixture_df)

    def test_filter_missing_columns(self):
        columns_to_check = [
            "is_pano",
            "organization_id",
            "captured_at",
        ]
        for column in columns_to_check:
            df_copy = self.fixture_df.copy()
            df_copy[column] = None

            filter_key = column
            if column == "is_pano":
                filter_key = "pano_only"
            elif column == "captured_at":
                filter_key = "start_time"

            result = filter_results(df_copy, **{filter_key: True})  # type: ignore[reportArgumentType]
            assert result is None

    @patch("project_types.street.api_calls.coordinate_download")
    def test_get_image_metadata(self, mock_coordinate_download):  # type: ignore[reportMissingParameterType]
        mock_coordinate_download.return_value = self.fixture_df
        result = get_image_metadata(aoi_geojson=self.fixture_data, provider=self.provider)
        assert sorted(result["feature_ids"]) == sorted(self.fixture_df["id"].tolist())
        assert len(result["features"]) == len(self.fixture_df)

    @patch("project_types.street.api_calls.coordinate_download")
    def test_get_image_metadata_empty_response(self, mock_coordinate_download):  # type: ignore[reportMissingParameterType]
        df = self.fixture_df.copy()
        df = df.drop(df.index)
        mock_coordinate_download.return_value = df

        with pytest.raises(ValidationException):
            get_image_metadata(aoi_geojson=self.fixture_data, provider=self.provider)

    @patch("project_types.street.api_calls.coordinate_download")
    def test_get_image_metadata_size_restriction(self, mock_coordinate_download):  # type: ignore[reportMissingParameterType]
        mock_df = pd.DataFrame(
            {
                "id": range(1, 100002),
                "geometry": range(1, 100002),
                "captured_at": pd.NaT,
                "sequence_id": 1,
            },
        )
        mock_coordinate_download.return_value = mock_df
        with pytest.raises(ValidationException, match="Too many Images"):
            get_image_metadata(aoi_geojson=self.fixture_data, provider=self.provider)

    @patch("project_types.street.api_calls.coordinate_download")
    def test_get_image_metadata_drop_duplicates(self, mock_coordinate_download):  # type: ignore[reportMissingParameterType]
        test_df = pd.DataFrame(
            {
                "id": [1, 2, 2, 3, 4, 4, 5],
                "geometry": ["a", "b", "b", "c", "d", "d", "e"],
                "sequence_id": [1, 1, 1, 1, 1, 1, 1],
                "captured_at": pd.to_datetime(["2020-01-01"] * 7),
            },
        )
        mock_coordinate_download.return_value = test_df
        result = get_image_metadata(aoi_geojson=self.fixture_data, provider=self.provider)

        assert sorted(result["feature_ids"]) == [1, 2, 3, 4, 5]
        assert sorted(result["features"]) == ["a", "b", "c", "d", "e"]


class TestStreetImageProviderConfig(unittest.TestCase):
    def test_provider_config_is_required(self):
        for provider in StreetImageProviderEnum:
            for data in [{"provider": provider}, {"provider": provider, provider.value: None}]:
                with pytest.raises(ValidationError, match=f"{provider.value} config is required"):
                    StreetImageProviderConfig.model_validate(data)

    def test_other_provider_configs_are_rejected(self):
        configs = {
            StreetImageProviderEnum.MAPILLARY: {},
            StreetImageProviderEnum.PANORAMAX: {},
            StreetImageProviderEnum.PANORAMAX_CUSTOM: {"url": "https://panoramax.example.com"},
        }
        for provider in StreetImageProviderEnum:
            for other_provider in StreetImageProviderEnum:
                if other_provider == provider:
                    continue
                data = {
                    "provider": provider,
                    provider.value: configs[provider],
                    other_provider.value: configs[other_provider],
                }
                with pytest.raises(ValidationError, match=f"{other_provider.value} config is only allowed"):
                    StreetImageProviderConfig.model_validate(data)

    def test_get_config(self):
        cases = [
            (StreetImageProviderEnum.MAPILLARY, {}, Config.MAPILLARY_API_LINK, 14),
            (StreetImageProviderEnum.PANORAMAX, {}, Config.PANORAMAX_API_LINK, 15),
            (
                StreetImageProviderEnum.PANORAMAX_CUSTOM,
                {"url": "https://panoramax.example.com"},
                "https://panoramax.example.com",
                15,
            ),
        ]
        for provider, config, expected_url, expected_tile_level in cases:
            assert get_provider_config(provider, **config) == {
                "name": provider,
                "url": expected_url,
                "tile_level": expected_tile_level,
            }

    def test_get_filters(self):
        filters = {
            "pano_only": True,
            "creator_id": "7",
            "start_time": "2024-01-01",
            "end_time": "2024-12-31",
            "randomize_order": True,
            "sampling_threshold": 100,
        }
        cases = [
            (StreetImageProviderEnum.MAPILLARY, {"organization_id": "42"}, "42"),
            (StreetImageProviderEnum.PANORAMAX, {}, None),
            (StreetImageProviderEnum.PANORAMAX_CUSTOM, {"url": "https://panoramax.example.com"}, None),
        ]
        for provider, config, expected_organization_id in cases:
            provider_config = StreetImageProviderConfig.model_validate(
                {"provider": provider, provider.value: {**filters, **config}},
            )
            assert provider_config.get_filters() == {**filters, "organization_id": expected_organization_id}

    def test_organization_id_only_for_mapillary(self):
        for provider, config in [
            (StreetImageProviderEnum.PANORAMAX, {}),
            (StreetImageProviderEnum.PANORAMAX_CUSTOM, {"url": "https://panoramax.example.com"}),
        ]:
            provider_config = StreetImageProviderConfig.model_validate(
                {"provider": provider, provider.value: {**config, "organization_id": "42"}},
            )
            assert provider_config.get_filters()["organization_id"] is None

    def test_sampling_threshold_must_be_a_non_negative_integer(self):
        for sampling_threshold in [0, 100]:
            provider_config = StreetImageProviderConfig.model_validate(
                {"provider": "mapillary", "mapillary": {"sampling_threshold": sampling_threshold}},
            )
            assert provider_config.get_filters()["sampling_threshold"] == sampling_threshold
        for sampling_threshold in [True, False, -1, 100.0]:
            with pytest.raises(ValidationError, match="sampling_threshold"):
                StreetImageProviderConfig.model_validate(
                    {"provider": "mapillary", "mapillary": {"sampling_threshold": sampling_threshold}},
                )

    def test_panoramax_custom_requires_url(self):
        for config in [{}, {"url": None}]:
            with pytest.raises(ValidationError, match="url"):
                get_provider_config(StreetImageProviderEnum.PANORAMAX_CUSTOM, **config)

    def test_panoramax_custom_url_is_kept_as_entered(self):
        for url in [
            "https://panoramax.example.com",
            "https://panoramax.example.com/",
            "http://localhost:8080",
            "https://panoramax.example.com:8443",
            "https://panoramax.example.com:8443/",
            "http://192.168.1.2",
        ]:
            assert get_provider_config(StreetImageProviderEnum.PANORAMAX_CUSTOM, url=url)["url"] == url

    def test_panoramax_custom_url_must_be_scheme_and_host(self):
        for url, message in [
            (" https://p.org", "url must not have leading or trailing whitespace"),
            ("https://p.org ", "url must not have leading or trailing whitespace"),
            ("\thttps://p.org", "url must not have leading or trailing whitespace"),
            ("https://p.org\n", "url must not have leading or trailing whitespace"),
            ("p.org", "url must start with http:// or https://"),
            ("ftp://p.org", "url must start with http:// or https://"),
            ("https://p.org/?", "url must not have a path, query or fragment"),
            ("https://p.org#", "url must not have a path, query or fragment"),
            ("https://p.org/?a=1", "url must not have a path, query or fragment"),
            ("https://p.org/#a", "url must not have a path, query or fragment"),
            ("https://p.org/a", "url must not have a path, query or fragment"),
            ("https://p.org/a/..", "url must not have a path, query or fragment"),
            ("https://p.org/api", "url must not have a path, query or fragment"),
            ("https://p.org//", "url must not have a path, query or fragment"),
            ("https://u:secret@p.org", "url must not have credentials"),
            ("https://p..org", "url must have a valid hostname or IPv4 address and an optional port"),
            ("https://256.1.1.1", "url must have a valid hostname or IPv4 address and an optional port"),
            ("https://p.org:0", "url must have a valid hostname or IPv4 address and an optional port"),
            ("https://p.org:65536", "url must have a valid hostname or IPv4 address and an optional port"),
            ("https://[::1]", "url must have a valid hostname or IPv4 address and an optional port"),
        ]:
            with pytest.raises(ValidationError, match=re.escape(message)):
                get_provider_config(StreetImageProviderEnum.PANORAMAX_CUSTOM, url=url)

    def test_panoramax_custom_url_must_not_be_too_long(self):
        url = f"https://{'a' * 1000}.example.com"
        with pytest.raises(ValidationError, match="String should have at most 1000 characters"):
            get_provider_config(StreetImageProviderEnum.PANORAMAX_CUSTOM, url=url)

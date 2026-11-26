import datetime
import io
import typing
from unittest.mock import MagicMock, patch

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from django.contrib.gis.geos import GEOSGeometry

from main.config import Config
from main.tests import TestCase
from project_types.validate.api_calls import (
    OHSOME_EXTRACTION_CONTRIBUTIONS_PATH,
    OHSOME_EXTRACTION_FEATURES_PATH,
    OHSOME_STATS_COUNT_PATH,
    ValidateApiCallError,
    add_changeset_tags,
    get_changeset_pages,
    get_object_count_from_ohsome,
    get_objects_from_ohsome,
    parquet_to_changeset_tags,
    parquet_to_feature_collection,
    remove_troublesome_chars,
)

# NOTE: Carries every column the API sends, so the tests also cover ignoring the rest.
# https://docs.ohsome.org/ohsome-api/v2-rc/reference/data_model.html
EXTRACTION_SCHEMA = pa.schema(
    [
        ("osm_type", pa.string()),
        ("osm_id", pa.int64()),
        ("edit_timestamp", pa.timestamp("us", tz="UTC")),
        ("valid_to_timestamp", pa.timestamp("us", tz="UTC")),
        ("version", pa.int32()),
        ("minor_version", pa.int32()),
        ("edits", pa.int32()),
        ("user_id", pa.int32()),
        ("user_name", pa.string()),
        ("changeset_id", pa.int64()),
        ("tags", pa.map_(pa.string(), pa.string())),
        (
            "bbox",
            pa.struct(
                [("xmin", pa.float64()), ("xmax", pa.float64()), ("ymin", pa.float64()), ("ymax", pa.float64())],
            ),
        ),
        ("geom_type", pa.string()),
        ("geom", pa.binary()),
        ("clipped", pa.bool_()),
    ],
)

# NOTE: The contributions extraction carries the features extraction columns and the
# contribution and changeset columns.
# https://docs.ohsome.org/ohsome-api/v2/reference/data_model.html
CONTRIBUTIONS_SCHEMA = pa.schema(
    [
        *EXTRACTION_SCHEMA,
        ("contribution_type", pa.string()),
        ("changeset_tags", pa.map_(pa.string(), pa.string())),
    ],
)


class TestValidateProject(TestCase):
    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_remove_troublesome_chars(self):
        data = [
            ("Hello\nWorld", "Hello World"),
            ('She said "Hello"', "She said Hello"),
            ("It's fine", "Its fine"),
            ("Hello 'World'", "Hello World"),
            (None, None),
            (123, 123),
        ]
        for input_str, expected in data:
            result = remove_troublesome_chars(input_str)
            assert result == expected

    @patch("requests.post")
    def test_get_object_count_from_ohsome(self, mock_post):  # type: ignore[reportMissingParameterType]
        sample_filter = "building=* and geometry:polygon"
        sample_aoi = {
            "type": "Polygon",
            "coordinates": [[[8.67, 49.39], [8.68, 49.39], [8.68, 49.40], [8.67, 49.40], [8.67, 49.39]]],
        }
        sample_object_count = 500

        # NOTE: The result is columnar, not a list of objects.
        mock_response_data = {
            "apiVersion": "2.0.0rc2",
            "attribution": {
                "url": "https://ohsome.org/copyrights",
                "text": "© OpenStreetMap contributors",
            },
            "result": {
                "timestamp": ["2026-09-07T07:05:05Z"],
                "value": [sample_object_count],
            },
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_post.return_value = mock_response

        object_count = get_object_count_from_ohsome(sample_aoi, sample_filter)

        assert object_count == sample_object_count
        mock_post.assert_called_once()

        # NOTE: Guards against a silent base-URL or endpoint-path regression
        called_url = mock_post.call_args[0][0]
        assert called_url == Config.OHSOME_API_LINK + OHSOME_STATS_COUNT_PATH
        assert called_url.startswith(Config.OHSOME_API_LINK)

        # v2 requires a JSON body, an explicit time and an API key
        called_kwargs = mock_post.call_args[1]
        assert called_kwargs["json"] == {
            "aoi": sample_aoi,
            "filter": sample_filter,
            "time": "latest",
        }
        assert called_kwargs["headers"]["Authorization"] == Config.OHSOME_API_KEY

    @patch("requests.post")
    def test_get_object_count_from_ohsome_empty_result(self, mock_post):  # type: ignore[reportMissingParameterType]
        """An empty result must return None rather than raising IndexError."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": {"timestamp": [], "value": []}}
        mock_post.return_value = mock_response

        assert get_object_count_from_ohsome({"type": "Polygon", "coordinates": []}, "building=*") is None

    @patch("requests.post")
    def test_get_object_count_from_ohsome_errors(self, mock_post):  # type: ignore[reportMissingParameterType]
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        for status_code in [400, 401, 403, 404, 422, 500]:
            mock_response.status_code = status_code
            with pytest.raises(ValidateApiCallError):
                get_object_count_from_ohsome({"type": "Polygon", "coordinates": []}, "building=*")

    @staticmethod
    def build_ohsome_parquet(rows: list[dict[str, typing.Any]] | None = None) -> bytes:
        """Build a parquet payload matching the ohsome v2 features extraction schema."""
        if rows is None:
            rows = [
                {
                    "osm_type": "way",
                    "osm_id": 500904926,
                    "version": 1,
                    "changeset_id": 49584905,
                    "edit_timestamp": datetime.datetime(2017, 6, 16, 9, 7, 24, tzinfo=datetime.UTC),
                    "user_id": 4204463,
                    "user_name": "Alisha12",
                    "geom": GEOSGeometry(
                        "POLYGON((85.3162 27.6718,85.3163 27.6718,85.3163 27.6719,85.3162 27.6719,85.3162 27.6718))",
                        srid=4326,
                    ).wkb.tobytes(),
                    "geom_type": "Polygon",
                },
            ]

        # NOTE: from_pylist nulls any column a row omits.
        table = pa.Table.from_pylist(rows, schema=EXTRACTION_SCHEMA)
        buffer = io.BytesIO()
        pq.write_table(table, buffer)
        return buffer.getvalue()

    def test_parquet_to_feature_collection(self):
        feature_collection = parquet_to_feature_collection(self.build_ohsome_parquet())

        assert feature_collection["type"] == "FeatureCollection"
        assert len(feature_collection["features"]) == 1

        feature = feature_collection["features"][0]
        assert feature["geometry"]["type"] == "Polygon"

        # NOTE: These names become columns of the public task CSV export.
        assert feature["properties"] == {
            "changesetId": 49584905,
            "lastEdit": "2017-06-16T09:07:24Z",
            "osmId": "way/500904926",
            "version": 1,
            "username": "Alisha12",
            "comment": None,
            "editor": None,
            "userid": 4204463,
        }
        # NOTE: jsonb storage, not this order, decides the real CSV column order.
        assert list(feature["properties"]) == [
            "changesetId",
            "lastEdit",
            "osmId",
            "version",
            "username",
            "comment",
            "editor",
            "userid",
        ]

    def test_parquet_to_feature_collection_missing_column(self):
        """A schema change upstream must fail loudly, not produce partial features."""
        table = pq.read_table(pa.BufferReader(self.build_ohsome_parquet()))
        buffer = io.BytesIO()
        pq.write_table(table.drop_columns(["changeset_id"]), buffer)

        with pytest.raises(ValidateApiCallError):
            parquet_to_feature_collection(buffer.getvalue())

    def test_parquet_to_feature_collection_scrubs_username(self):
        rows = [
            {
                "osm_type": "relation",
                "osm_id": 42,
                "version": 3,
                "changeset_id": 777,
                "edit_timestamp": datetime.datetime(2020, 1, 2, 3, 4, 5, tzinfo=datetime.UTC),
                "user_id": 9,
                "user_name": "Shyam 'Bahadur'",
                "geom": GEOSGeometry("POLYGON((0 0,1 0,1 1,0 1,0 0))", srid=4326).wkb.tobytes(),
                "geom_type": "Polygon",
            },
        ]
        properties = parquet_to_feature_collection(self.build_ohsome_parquet(rows))["features"][0]["properties"]

        assert properties["username"] == "Shyam Bahadur"
        assert properties["osmId"] == "relation/42"

    @patch("requests.post")
    @patch("project_types.validate.api_calls.add_changeset_tags")
    def test_get_objects_from_ohsome(self, mock_add_changeset_tags, mock_post):  # type: ignore[reportMissingParameterType]
        sample_filter = "building=* and geometry:polygon"
        sample_aoi = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = self.build_ohsome_parquet()
        mock_post.return_value = mock_response
        mock_add_changeset_tags.side_effect = lambda _aoi, _filter, feature_collection: feature_collection

        result = get_objects_from_ohsome(sample_aoi, sample_filter)

        mock_post.assert_called_once()
        assert mock_post.call_args[0][0] == Config.OHSOME_API_LINK + OHSOME_EXTRACTION_FEATURES_PATH

        called_kwargs = mock_post.call_args[1]
        assert called_kwargs["json"] == {
            "aoi": sample_aoi,
            "filter": sample_filter,
            "time": "latest",
            "clip": False,
        }
        assert called_kwargs["headers"]["Authorization"] == Config.OHSOME_API_KEY

        # NOTE: The contributions are requested with the same aoi and filter
        mock_add_changeset_tags.assert_called_once()
        assert mock_add_changeset_tags.call_args[0][:2] == (sample_aoi, sample_filter)
        assert len(result["features"]) == 1

        for status_code in [400, 401, 403, 404, 422, 500]:
            mock_response.status_code = status_code
            with pytest.raises(ValidateApiCallError):
                get_objects_from_ohsome(sample_aoi, sample_filter)

    @staticmethod
    def build_contributions_parquet(rows: list[dict[str, typing.Any]]) -> bytes:
        """Build a parquet payload matching the ohsome v2 contributions extraction schema."""
        table = pa.Table.from_pylist(rows, schema=CONTRIBUTIONS_SCHEMA)
        buffer = io.BytesIO()
        pq.write_table(table, buffer)
        return buffer.getvalue()

    @staticmethod
    def build_contribution(
        osm_id: int,
        changeset_id: int,
        changeset_tags: dict[str, str] | None,
        **kwargs: typing.Any,
    ) -> dict[str, typing.Any]:
        return {
            "osm_type": "way",
            "osm_id": osm_id,
            "changeset_id": changeset_id,
            # NOTE: from_pylist takes a map value as a list of (key, value) pairs
            "changeset_tags": None if changeset_tags is None else list(changeset_tags.items()),
            "contribution_type": "CREATION",
            **kwargs,
        }

    @staticmethod
    def build_feature(osm_id: int, changeset_id: int, last_edit: str | None) -> dict[str, typing.Any]:
        return {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [0, 0]},
            "properties": {
                "changesetId": changeset_id,
                "lastEdit": last_edit,
                "osmId": f"way/{osm_id}",
                "version": 1,
                "username": "Sita",
                "comment": None,
                "editor": None,
                "userid": 1001,
            },
        }

    def test_parquet_to_changeset_tags(self):
        content = self.build_contributions_parquet(
            [
                self.build_contribution(1, 100, {"comment": "Add buildings", "created_by": "iD 2.20"}),
                self.build_contribution(2, 200, {"source": "Bing"}),
                self.build_contribution(3, 300, None),
            ],
        )

        assert parquet_to_changeset_tags(content) == {
            ("way/1", 100): {"comment": "Add buildings", "created_by": "iD 2.20"},
            ("way/2", 200): {"source": "Bing"},
            ("way/3", 300): {},
        }

    def test_parquet_to_changeset_tags_missing_column(self):
        """A schema change upstream must fail loudly, not leave every comment and editor empty."""
        content = self.build_contributions_parquet([self.build_contribution(1, 100, {"comment": "Add buildings"})])
        table = pq.read_table(pa.BufferReader(content))
        buffer = io.BytesIO()
        pq.write_table(table.drop_columns(["changeset_tags"]), buffer)

        with pytest.raises(ValidateApiCallError):
            parquet_to_changeset_tags(buffer.getvalue())

    def test_get_changeset_pages(self):
        feature_collection = {
            "type": "FeatureCollection",
            "features": [
                self.build_feature(1, 300, "2021-01-01T00:00:00Z"),
                self.build_feature(2, 100, "2019-05-05T10:00:00Z"),
                # NOTE: The oldest edit of a changeset orders it
                self.build_feature(3, 300, "2018-01-01T00:00:00Z"),
                self.build_feature(4, 200, "2020-01-01T00:00:00Z"),
                self.build_feature(5, 400, "2022-01-01T00:00:00Z"),
            ],
        }

        assert get_changeset_pages(feature_collection) == [("2018-01-01T00:00:00Z", [300, 100, 200, 400])]

        with patch("project_types.validate.api_calls.OHSOME_CHANGESET_PAGE_SIZE", 2):
            assert get_changeset_pages(feature_collection) == [
                ("2018-01-01T00:00:00Z", [300, 100]),
                ("2020-01-01T00:00:00Z", [200, 400]),
            ]

        assert get_changeset_pages({"type": "FeatureCollection", "features": []}) == []

    def test_get_changeset_pages_without_last_edit(self):
        feature_collection = {
            "type": "FeatureCollection",
            "features": [
                self.build_feature(1, 100, "2019-05-05T10:00:00Z"),
                self.build_feature(2, 200, None),
            ],
        }

        assert get_changeset_pages(feature_collection) == [("earliest", [200, 100])]

    @patch("requests.post")
    def test_add_changeset_tags(self, mock_post):  # type: ignore[reportMissingParameterType]
        sample_filter = "building=* and geometry:polygon"
        sample_aoi = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}
        feature_collection = {
            "type": "FeatureCollection",
            "features": [
                self.build_feature(1, 100, "2019-05-05T10:00:00Z"),
                self.build_feature(2, 200, "2020-01-01T00:00:00Z"),
                self.build_feature(3, 300, "2018-01-01T00:00:00Z"),
                self.build_feature(4, 400, "2021-01-01T00:00:00Z"),
            ],
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = self.build_contributions_parquet(
            [
                self.build_contribution(1, 100, {"comment": 'It\'s a "school"', "created_by": "JOSM/1.5"}),
                # NOTE: An older contribution of the same object, in another changeset
                self.build_contribution(1, 50, {"comment": "Old", "created_by": "Potlatch"}),
                self.build_contribution(2, 200, {"source": "Bing"}),
                # NOTE: Another object of changeset 300; the feature's own contribution is missing
                self.build_contribution(99, 300, {"comment": "Other object", "created_by": "iD"}),
            ],
        )
        mock_post.return_value = mock_response

        result = add_changeset_tags(sample_aoi, sample_filter, feature_collection)

        mock_post.assert_called_once()
        assert mock_post.call_args[0][0] == Config.OHSOME_API_LINK + OHSOME_EXTRACTION_CONTRIBUTIONS_PATH
        called_kwargs = mock_post.call_args[1]
        assert called_kwargs["json"] == {
            "aoi": sample_aoi,
            "filter": "(building=* and geometry:polygon) and changeset:(300,100,200,400)",
            "time": {"start": "2018-01-01T00:00:00Z", "end": "latest"},
        }
        assert called_kwargs["headers"]["Authorization"] == Config.OHSOME_API_KEY

        assert [(feature["properties"]["comment"], feature["properties"]["editor"]) for feature in result["features"]] == [
            ("Its a school", "JOSM/1.5"),
            # NOTE: The changeset has no comment or created_by tag
            (None, None),
            # NOTE: Joined on osmId and changesetId, not changesetId alone
            (None, None),
            # NOTE: No contribution returned
            (None, None),
        ]

        # NOTE: The other columns come from the features extraction and are kept
        assert result["features"][0]["properties"]["username"] == "Sita"
        assert result["features"][0]["properties"]["userid"] == 1001

    @patch("requests.post")
    def test_add_changeset_tags_in_pages(self, mock_post):  # type: ignore[reportMissingParameterType]
        feature_collection = {
            "type": "FeatureCollection",
            "features": [
                self.build_feature(1, 100, "2019-01-01T00:00:00Z"),
                self.build_feature(2, 200, "2020-01-01T00:00:00Z"),
                self.build_feature(3, 300, "2021-01-01T00:00:00Z"),
            ],
        }

        def respond(*_args: typing.Any, **kwargs: typing.Any) -> MagicMock:
            changeset_ids = kwargs["json"]["filter"].split("changeset:(")[1].rstrip(")").split(",")
            response = MagicMock()
            response.status_code = 200
            response.content = self.build_contributions_parquet(
                [
                    self.build_contribution(int(changeset_id) // 100, int(changeset_id), {"comment": changeset_id})
                    for changeset_id in changeset_ids
                ],
            )
            return response

        mock_post.side_effect = respond

        with patch("project_types.validate.api_calls.OHSOME_CHANGESET_PAGE_SIZE", 2):
            result = add_changeset_tags({"type": "Polygon", "coordinates": []}, "building=*", feature_collection)

        assert [call[1]["json"]["time"]["start"] for call in mock_post.call_args_list] == [
            "2019-01-01T00:00:00Z",
            "2021-01-01T00:00:00Z",
        ]
        assert [feature["properties"]["comment"] for feature in result["features"]] == ["100", "200", "300"]

    @patch("requests.post")
    def test_add_changeset_tags_no_features(self, mock_post):  # type: ignore[reportMissingParameterType]
        result = add_changeset_tags({"type": "Polygon", "coordinates": []}, "building=*", {"features": []})

        assert result["features"] == []
        mock_post.assert_not_called()

    @patch("requests.post")
    def test_add_changeset_tags_errors(self, mock_post):  # type: ignore[reportMissingParameterType]
        feature_collection = {"features": [self.build_feature(1, 100, "2019-01-01T00:00:00Z")]}
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        for status_code in [400, 401, 403, 404, 413, 422, 429, 500, 504]:
            mock_response.status_code = status_code
            with pytest.raises(ValidateApiCallError):
                add_changeset_tags({"type": "Polygon", "coordinates": []}, "building=*", feature_collection)

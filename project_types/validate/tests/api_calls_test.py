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
    OHSOME_EXTRACTION_FEATURES_PATH,
    OHSOME_STATS_COUNT_PATH,
    ValidateApiCallError,
    add_changeset_info,
    get_object_count_from_ohsome,
    get_objects_from_ohsome,
    parquet_to_feature_collection,
    query_osm,
    query_osmcha,
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

    @patch("project_types.validate.api_calls.retry_get")
    def test_query_osmcha(self, mock_retry_get):  # type: ignore[reportMissingParameterType]
        changeset_ids = [12345, 67890]
        changeset_results = {}

        # Fake API JSON response
        mock_response_data = {
            "features": [
                {
                    "id": "12345",
                    "properties": {
                        "user": "Sita Devi",
                        "uid": 1001,
                        "comment": "Looks good!",
                        "editor": "Ram",
                    },
                },
                {
                    "id": "67890",
                    "properties": {
                        "user": "Hari",
                        "uid": 1002,
                        "comment": "It's not a bridge",
                        "editor": "Shyam 'Bahadur'",
                    },
                },
            ],
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_retry_get.return_value = mock_response

        query_osmcha(changeset_ids, changeset_results)

        assert changeset_results == {
            12345: {
                "username": "Sita Devi",
                "userid": 1001,
                "comment": "Looks good!",
                "editor": "Ram",
            },
            67890: {
                "username": "Hari",
                "userid": 1002,
                "comment": "Its not a bridge",
                "editor": "Shyam Bahadur",
            },
        }

        # Check request is made for osmcha
        mock_retry_get.assert_called_once()
        called_url = mock_retry_get.call_args[0][0]
        assert called_url.startswith(Config.OSMCHA_API_LINK)
        assert "changesets/?ids=12345,67890" in called_url

        # check for other status code to raise error
        mock_response.status_code = 403
        with pytest.raises(ValidateApiCallError):
            query_osmcha(changeset_ids, changeset_results)

    @patch("project_types.validate.api_calls.retry_get")
    def test_query_osm(self, mock_retry_get):  # type: ignore[reportMissingParameterType]
        changeset_ids = [12345, 67890]
        changeset_results = {}

        xml_response = """
        <osm>
            <changeset id="12345" user='Sita "Devi"' uid="1001">
                <tag k="comment" v="Looks good!"/>
                <tag k="created_by" v="Ram"/>
            </changeset>
            <changeset id="67890" user="Hari" uid="1002">
                <tag k="comment" v="It's not a bridge"/>
                <tag k="created_by" v="Shyam Bahadur"/>
            </changeset>
        </osm>
        """

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = xml_response.encode("utf-8")
        mock_retry_get.return_value = mock_response

        result = query_osm(changeset_ids, changeset_results)

        assert result == {
            12345: {
                "username": "Sita Devi",
                "userid": "1001",
                "comment": "Looks good!",
                "editor": "Ram",
            },
            67890: {
                "username": "Hari",
                "userid": "1002",
                "comment": "Its not a bridge",
                "editor": "Shyam Bahadur",
            },
        }

        # check for other status code to raise error
        mock_response.status_code = 500
        with pytest.raises(ValidateApiCallError):
            query_osm([12345], {})

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
    @patch("project_types.validate.api_calls.add_changeset_info")
    def test_get_objects_from_ohsome(self, mock_add_changeset_info, mock_post):  # type: ignore[reportMissingParameterType]
        sample_filter = "building=* and geometry:polygon"
        sample_aoi = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = self.build_ohsome_parquet()
        mock_post.return_value = mock_response
        mock_add_changeset_info.side_effect = lambda feature_collection: feature_collection

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

        mock_add_changeset_info.assert_called_once()
        assert len(result["features"]) == 1

        for status_code in [400, 401, 403, 404, 422, 500]:
            mock_response.status_code = status_code
            with pytest.raises(ValidateApiCallError):
                get_objects_from_ohsome(sample_aoi, sample_filter)

    @staticmethod
    def build_feature_collection(*changeset_ids: int) -> dict[str, typing.Any]:
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [0, 0]},
                    "properties": {
                        "osmId": f"way/{changeset_id}",
                        "version": 1,
                        "changesetId": changeset_id,
                        "lastEdit": "2020-01-01T00:00:00Z",
                        "username": "Sita",
                        "userid": 1001,
                    },
                }
                for changeset_id in changeset_ids
            ],
        }

    @patch("project_types.validate.api_calls.query_osm")
    @patch("project_types.validate.api_calls.query_osmcha")
    def test_add_changeset_info(self, mock_query_osmcha, mock_query_osm):  # type: ignore[reportMissingParameterType]
        feature_collection = self.build_feature_collection(12345, 12346)

        # osmCHA resolves the first changeset only
        mock_query_osmcha.return_value = {
            12345: {"username": "Sita", "userid": 1001, "comment": "Looks good!", "editor": "iD"},
            12346: None,
        }
        # the OSM API fallback resolves the second
        mock_query_osm.return_value = {
            12345: {"username": "Sita", "userid": 1001, "comment": "Looks good!", "editor": "iD"},
            12346: {"username": "Kiran", "userid": 1002, "comment": "Fixed roof", "editor": "JOSM"},
        }

        result = add_changeset_info(feature_collection)

        mock_query_osmcha.assert_called()
        assert set(mock_query_osmcha.call_args[0][0]) == {12345, 12346}
        # only the changeset osmCHA could not resolve is retried against the OSM API
        mock_query_osm.assert_called_once()
        assert set(mock_query_osm.call_args[0][0]) == {12346}

        first, second = result["features"]
        assert (first["properties"]["comment"], first["properties"]["editor"]) == ("Looks good!", "iD")
        assert (second["properties"]["comment"], second["properties"]["editor"]) == ("Fixed roof", "JOSM")

        # username/userid come from the ohsome extraction and must not be overwritten
        assert first["properties"]["username"] == "Sita"
        assert first["properties"]["userid"] == 1001

    @patch("project_types.validate.api_calls.query_osm")
    @patch("project_types.validate.api_calls.query_osmcha")
    def test_add_changeset_info_unresolved(self, mock_query_osmcha, mock_query_osm):  # type: ignore[reportMissingParameterType]
        """A changeset neither source knows about must not raise."""
        feature_collection = self.build_feature_collection(999)
        mock_query_osmcha.return_value = {999: None}
        mock_query_osm.return_value = {999: None}

        result = add_changeset_info(feature_collection)

        properties = result["features"][0]["properties"]
        assert properties["comment"] is None
        assert properties["editor"] is None

    @patch("project_types.validate.api_calls.query_osm")
    @patch("project_types.validate.api_calls.query_osmcha")
    def test_add_changeset_info_no_features(self, mock_query_osmcha, mock_query_osm):  # type: ignore[reportMissingParameterType]
        result = add_changeset_info(self.build_feature_collection())

        assert result["features"] == []
        mock_query_osmcha.assert_not_called()
        mock_query_osm.assert_not_called()

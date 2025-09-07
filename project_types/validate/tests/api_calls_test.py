import typing
from unittest.mock import MagicMock, patch

import pytest

from main.config import Config
from main.tests import TestCase
from project_types.validate.api_calls import (
    ValidateApiCallError,
    ohsome,
    query_osm,
    query_osmcha,
    remove_noise_and_add_user_info,
    remove_troublesome_chars,
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
    def test_query_osmcha(self, mock_retry_get):
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
    def test_query_osm(self, mock_retry_get):
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
    @patch("project_types.validate.api_calls.remove_noise_and_add_user_info")
    def test_ohsome(self, mock_remove_noise, mock_post):
        sample_request = {
            "endpoint": "elements/geometry",
            "filter": "highway=primary",
        }
        sample_area = "POLYGON((8.67 49.39,8.68 49.39,8.68 49.40,8.67 49.40,8.67 49.39))"
        sample_properties = "tags,timestamp"

        mock_response_data = {
            "attribution": {
                "url": "https://ohsome.org/copyrights",
                "text": "© OpenStreetMap contributors",
            },
            "apiVersion": "1.10.4",
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            8.6861,
                            49.4051089,
                        ],
                    },
                    "properties": {
                        "@osmId": "node/385941986",
                        "@snapshotTimestamp": "2019-09-01T00: 00: 00Z",
                    },
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            8.6819524,
                            49.3825748,
                        ],
                    },
                    "properties": {
                        "@osmId": "node/699583613",
                        "@snapshotTimestamp": "2019-09-01T00: 00: 00Z",
                    },
                },
            ],
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_post.return_value = mock_response

        processed_data = {"processed": True, "data": mock_response_data}
        mock_remove_noise.return_value = processed_data

        result = ohsome(sample_request, sample_area, sample_properties)

        mock_post.assert_called_once()
        mock_remove_noise.assert_called_once_with(mock_response_data)
        assert result == processed_data

        # test for error
        status_codes = [400, 401, 403, 404, 500]
        for status_code in status_codes:
            mock_response.status_code = status_code
            with pytest.raises(ValidateApiCallError):
                result = ohsome(sample_request, sample_area, sample_properties)

    @patch("project_types.validate.api_calls.query_osmcha")
    @patch("project_types.validate.api_calls.query_osm")
    def test_remove_noise_and_add_user_info(self, mock_query_osm, mock_query_osmcha):
        input_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [0, 0]},
                    "properties": {
                        "@changesetId": 12345,
                        "@lastEdit": 1234567890,
                        "@osmId": 111,
                        "@version": 1,
                        "unwanted_field": "should_be_removed",
                        "another_noise": 999,
                    },
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [1, 1]},
                    "properties": {
                        "@changesetId": 12346,
                        "@lastEdit": 1234567891,
                        "@osmId": 222,
                        "@version": 2,
                        "extra_data": "also_removed",
                    },
                },
            ],
        }
        mock_osmcha_response = {
            12345: {
                "username": "Sita",
                "comment": "This is a test comment",
                "editor": "iD",
                "userid": 1001,
            },
            12346: None,
        }

        mock_query_osmcha.return_value = mock_osmcha_response

        mock_query_osm.return_value = {
            12345: {
                "username": "Sita",
                "userid": "1001",
                "comment": "This is an updated test comment",
                "editor": "Ram",
            },
            12346: {
                "username": "Kiran",
                "userid": "1002",
                "comment": "This is a test comment",
                "editor": "Hari",
            },
        }

        remove_noise_and_add_user_info(input_data)
        mock_query_osmcha.assert_called()
        called_ids = mock_query_osmcha.call_args[0][0]
        assert set(called_ids) == {12345, 12346}
        mock_query_osm.assert_called()

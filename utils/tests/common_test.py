import gzip
import json
import typing

import pytest
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from pydantic_core import ValidationError as PydanticValidationError

from main.tests import TestCase
from utils.common import (
    compress_tasks,
    gzip_str,
    parse_b64gzjson_to_dict,
    validate_geojson_file,
    validate_imagery_url,
    validate_ulid,
)
from utils.fields import (
    _validate_raster_tile_url,  # type: ignore[reportPrivateUsage]
    _validate_url,  # type: ignore[reportPrivateUsage]
    _validate_vector_tile_url,  # type: ignore[reportPrivateUsage]
    validate_percentage,
)


class TestUtils(TestCase):
    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_validate_imagery_url(self):
        """Test valid XYZ tile URL format."""
        # test valid urls
        valid_urls = [
            "https://example.com/tiles/{x}/{y}/{z}.jpg",
            "https://tileserver.com/tiles/{z}/{x}/{-y}.png",
            "https://tileserver.com/tiles/{quad_key}.png",
        ]
        for url in valid_urls:
            validate_imagery_url(url)

        url = "https://tileserver.com/tiles/invalid.png"
        with pytest.raises(ValidationError):
            validate_imagery_url(url)

        url = "https://tileserver.com/tiles/invalid.png"
        with pytest.raises(ValidationError):
            validate_imagery_url(url, support_quad_key=True)

        url = "https://tileserver.com/tiles/{a}/{b}/{c}.png"
        with pytest.raises(ValidationError):
            validate_imagery_url(url, support_quad_key=False)

    def test_validate_ulid(self):
        # test valid ulid
        val = "01K1YXXF0MH0JXXJEVXQDPME8F"
        validate_ulid(val)

        # test for invalid ulids
        values = ["", "Jhon Doe", "accXYXAM23"]
        for value in values:
            with pytest.raises(ValidationError):
                validate_ulid(value)

    def test_validate_geo_json_file(self):
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-74.0060, 40.7128],
                    },
                    "properties": {
                        "name": "New York City Hall",
                        "amenity": "city_hall",
                    },
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [-73.9900, 40.7500],
                            [-73.9850, 40.7550],
                            [-73.9800, 40.7600],
                        ],
                    },
                    "properties": {
                        "name": "Broadway",
                        "type": "street",
                    },
                },
            ],
        }
        file_content = json.dumps(geojson_data)
        file = ContentFile(file_content.encode(), name="test.geojson")
        validate_geojson_file(file)

        # test invalid json
        invalid_json = '{"type": "FeatureCollection", "features": [invalid json}'
        file = ContentFile(invalid_json.encode(), name="test.geojson")
        with pytest.raises(ValidationError):
            validate_geojson_file(file)

        # test invalid geojson
        # polygon with insufficient coordinates
        invalid_geojson = {
            "type": "FeatureCollection",
            "geometry": {
                "type": "Polygon",
                # polygon requires at least 4 coordinate pairs (including closing)
                "coordinates": [
                    [
                        [-122.4194, 37.7749],
                        [-122.4094, 37.7749],
                    ],
                ],
            },
            "properties": {},
        }

        file_content = json.dumps(invalid_geojson)
        file = ContentFile(file_content.encode(), name="test.geojson")
        with pytest.raises(PydanticValidationError):
            validate_geojson_file(file)

        # test empty geojson features
        geojson_data = {
            "type": "FeatureCollection",
            "features": [],
        }
        file_content = json.dumps(geojson_data)
        file = ContentFile(file_content.encode(), name="test.geojson")
        with pytest.raises(ValidationError):
            validate_geojson_file(file)

    def test_gzip_str(self):
        test_string = "This is a test string." * 1000
        compressed = gzip_str(test_string)
        assert isinstance(compressed, bytes)
        # Compressed size should be significantly smaller than original
        original_size = len(test_string.encode())
        compressed_size = len(compressed)
        assert compressed_size < original_size
        # Should decompress correctly
        decompressed = gzip.decompress(compressed).decode()
        assert decompressed == test_string

    def test_compress_tasks(self):
        original_data = [
            {
                "project_id": 1,
                "name": "Task One",
                "status": "draft",
            },
            {
                "project_id": 2,
                "name": "Task Two",
                "status": "in_progress",
            },
        ]
        expected_output = "H4sIAAAAAAAC/4uuViooys9KTS6Jz0xRslIw1FFQykvMTQUylUISi7MV/PNSlYBixSWJJaXFINGUosS0EqVaHQU0nUboOkPK81F1ZubFA3WkF6UWFyvVxgIAaNCXhXoAAAA="  # noqa: E501
        result = compress_tasks(original_data)
        assert result == expected_output
        decompressed = parse_b64gzjson_to_dict(result)
        assert decompressed == original_data

        # test empty list
        tasks = []
        result = compress_tasks(tasks)
        assert result is not None

    def test_validate_url(self):
        encoded_url = "https://test.com/tiles/%7Bx%7D/%7By%7D/%7Bz%7D.png"
        expected_url = "https://test.com/tiles/{x}/{y}/{z}.png"
        assert _validate_url(encoded_url) == expected_url

        encoded_url = "https://test.com/tiles/{x}/{y}/{z}.png"
        expected_url = "https://test.com/tiles/{x}/{y}/{z}.png"
        assert _validate_url(encoded_url) == expected_url

    def test_validate_raster_tile_url(self):
        # test with valid url
        url = "https://example.com/tiles/{x}/{y}/{z}.jpg"
        _validate_raster_tile_url(url)

        # test with quad_key in url
        url = "https://tileserver.com/tiles/{quad_key}.png"
        _validate_raster_tile_url(url)

        # test invalid url
        url = "https://tileserver.com/{z}/{x}/{y}.png?foo={{y}}"
        with pytest.raises(ValidationError):
            _validate_raster_tile_url(url)

        # test for url without {y} only {x} and {z}
        url = "https://example.com/tiles/{x}/{z}.jpd"
        with pytest.raises(ValidationError):
            _validate_raster_tile_url(url)

    def test_valid_vector_tile_urls(self):
        url = "https://tileserver.com/{z}/{x}/{y}.pbf"
        _validate_vector_tile_url(url)

        # test invalid url
        url = "https://tileserver.com/{{x}}/{{y}}/{{z}}.pbf"
        with pytest.raises(ValidationError):
            _validate_vector_tile_url(url)

        # test url with quad_key should throw value error
        url = "https://tileserver.com/tiles/{quad_key}.png"
        with pytest.raises(ValidationError):
            _validate_vector_tile_url(url)

    def test_validate_percentage(self):
        values = [1, 10, 50, 100]
        for value in values:
            validate_percentage(value)
        # test for invalid value
        values = [-5, 101, 1000]
        for value in values:
            with pytest.raises(ValidationError):
                validate_percentage(value)

    def test_parse_b64gzjson_to_dict(self):
        original_json = [{"id": 1, "name": "Jhon Doe", "occupation": "Developer"}]
        compressed_task = compress_tasks(original_json)
        result = parse_b64gzjson_to_dict(compressed_task)
        assert result == original_json

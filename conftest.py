from urllib.parse import urlparse, urlunparse

import pytest
from django.http import QueryDict


def scrub_auth_token(request):  # type: ignore[reportMissingParameterType]
    # NOTE: We want to redact sensitize information from "Authorization: Token XYZ"
    authorization_header = request.headers.get("authorization")
    if authorization_header and authorization_header.lower().startswith("token"):
        request.headers["authorization"] = "Token DUMMY_TOKEN"

    url = request.uri
    if "access_token" in url:
        parsed_url = urlparse(url)

        query_dict = QueryDict(parsed_url.query, mutable=True)
        query_dict["access_token"] = "DUMMY_TOKEN"  # noqa: S105
        new_query = query_dict.urlencode()

        new_url = urlunparse(parsed_url._replace(query=new_query))
        request.uri = new_url
    return request


@pytest.fixture(autouse=True)
def vcr_config(request):  # type: ignore[reportMissingParameterType]
    marker = request.node.get_closest_marker("vcr")

    cassette_path = None
    if marker and marker.args:
        cassette_path = marker.args[0]

    return {
        "record_mode": "once",
        "ignore_hosts": ["localhost", "firebase-test"],
        "ignore_localhost": True,
        "cassette_library_dir": cassette_path or "assets/tests/tests_vcr_snapshots",
        "before_record_request": scrub_auth_token,
    }

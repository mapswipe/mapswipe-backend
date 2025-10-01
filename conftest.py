import pytest


@pytest.fixture(autouse=True)
def vcr_config(request):
    marker = request.node.get_closest_marker("vcr")

    cassette_path = None
    if marker and marker.args:
        cassette_path = marker.args[0]

    return {
        "record_mode": "once",
        "ignore_hosts": ["localhost", "firebase-test"],
        "ignore_localhost": True,
        "cassette_library_dir": cassette_path or "assets/tests/tests_vcr_snapshots",
    }

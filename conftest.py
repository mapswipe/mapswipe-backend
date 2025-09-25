import pytest


@pytest.fixture(autouse=True)
def vcr_config():
    return {
        "record_mode": "once",
        "ignore_hosts": ["localhost", "firebase-test"],
        "ignore_localhost": True,
        "cassette_library_dir": "assets/tests/tests_vcr_snapshots",
    }

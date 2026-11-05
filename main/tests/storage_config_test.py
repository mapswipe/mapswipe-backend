import base64
import gc
import gzip
import json
import typing
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage, storages
from django.db.models.fields.files import FieldFile
from django.test import SimpleTestCase, override_settings
from django.utils.module_loading import import_string
from google.auth.credentials import AnonymousCredentials
from google.oauth2.service_account import Credentials

from apps.common.utils import get_absolute_uri
from apps.project.models import ProjectAsset
from main.checks import short_term_storage_check
from main.config import Config
from main.fields import (
    OverwritableFileField,
    ShortTermFileField,
    _lazy_storages,  # type: ignore[reportPrivateUsage]
)
from main.storage_backends import GoogleCloudStorage
from main.storage_config import (
    DEFAULT_STORAGE_KEY,
    FILESYSTEM_BACKEND,
    GCS_BACKEND,
    S3_BACKEND,
    SHORT_TERM_STORAGE_KEY,
    STATICFILES_FILESYSTEM_BACKEND,
    STATICFILES_STORAGE_KEY,
    STORAGE_OVERWRITE_KEY,
    build_storage_settings,
    get_s3_endpoint_url,
)

BASE_DIR = Path("/code")
DEFAULT_DOMAIN = "https://api.example.org"


def build(environ_: dict[str, str]):
    return build_storage_settings(environ_, base_dir=BASE_DIR, default_domain=DEFAULT_DOMAIN)


def s3_env(prefix: str, bucket_name: str) -> dict[str, str]:
    return {
        f"{prefix}_BACKEND": "s3",
        f"{prefix}_S3_ENDPOINT_URL": "http://minio:9000",
        f"{prefix}_S3_ACCESS_KEY_ID": "access-key",
        f"{prefix}_S3_SECRET_ACCESS_KEY": "secret-key",
        f"{prefix}_S3_REGION_NAME": "us-east-1",
        f"{prefix}_S3_BUCKET_NAME": bucket_name,
    }


def s3_options(bucket_name: str) -> dict[str, typing.Any]:
    return {
        "endpoint_url": "http://minio:9000",
        "access_key": "access-key",
        "secret_key": "secret-key",
        "region_name": "us-east-1",
        "bucket_name": bucket_name,
        "querystring_auth": False,
    }


def fake_service_account_b64_gz() -> str:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    service_account_info = {
        "type": "service_account",
        "project_id": "fake-project",
        "private_key_id": "fake-key-id",
        "private_key": private_key_pem,
        "client_email": "storage@fake-project.iam.gserviceaccount.com",
        "client_id": "1234",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    return base64.b64encode(gzip.compress(json.dumps(service_account_info).encode())).decode()


class TestBuildStorageSettings(SimpleTestCase):
    def test_filesystem_defaults(self):
        storage_settings = build({"SHORT_TERM_STORAGE_ENABLED": "false"})

        assert storage_settings.storages == {
            DEFAULT_STORAGE_KEY: {
                "BACKEND": FILESYSTEM_BACKEND,
                "OPTIONS": {"domain": DEFAULT_DOMAIN},
            },
            STORAGE_OVERWRITE_KEY: {
                "BACKEND": FILESYSTEM_BACKEND,
                "OPTIONS": {"domain": DEFAULT_DOMAIN, "allow_overwrite": True},
            },
            STATICFILES_STORAGE_KEY: {"BACKEND": STATICFILES_FILESYSTEM_BACKEND},
        }
        assert storage_settings.short_term_enabled is False
        assert storage_settings.media_root == "/code/.data/media"
        assert storage_settings.media_url == "media/"
        assert storage_settings.media_domain == DEFAULT_DOMAIN
        assert storage_settings.static_root == "/code/.data/static"
        assert storage_settings.static_url == "static/"

    def test_filesystem_custom(self):
        storage_settings = build(
            {
                "MEDIA_STORAGE_BACKEND": "filesystem",
                "MEDIA_STORAGE_FS_ROOT": "/data/media",
                "MEDIA_STORAGE_FS_URL": "/m/",
                "MEDIA_STORAGE_FS_DOMAIN": "https://media.example.org/",
                "STATIC_STORAGE_FS_ROOT": "/data/static",
                "STATIC_STORAGE_FS_URL": "/s/",
                "SHORT_TERM_STORAGE_BACKEND": "filesystem",
                "SHORT_TERM_STORAGE_FS_ROOT": "/data/short-term",
                "SHORT_TERM_STORAGE_FS_URL": "/st/",
                "SHORT_TERM_STORAGE_FS_DOMAIN": "https://short-term.example.org",
            },
        )

        assert storage_settings.short_term_enabled is True
        assert storage_settings.media_root == "/data/media"
        assert storage_settings.media_url == "/m/"
        assert storage_settings.media_domain == "https://media.example.org"
        assert storage_settings.static_root == "/data/static"
        assert storage_settings.static_url == "/s/"
        assert storage_settings.storages[DEFAULT_STORAGE_KEY] == {
            "BACKEND": FILESYSTEM_BACKEND,
            "OPTIONS": {"domain": "https://media.example.org"},
        }
        assert storage_settings.storages[SHORT_TERM_STORAGE_KEY] == {
            "BACKEND": FILESYSTEM_BACKEND,
            "OPTIONS": {
                "location": "/data/short-term",
                "base_url": "/st/",
                "domain": "https://short-term.example.org",
                "allow_overwrite": True,
            },
        }

    def test_short_term_filesystem_defaults(self):
        storage_settings = build({"SHORT_TERM_STORAGE_BACKEND": "filesystem"})

        assert storage_settings.storages[SHORT_TERM_STORAGE_KEY] == {
            "BACKEND": FILESYSTEM_BACKEND,
            "OPTIONS": {
                "location": "/code/.data/short-term",
                "base_url": "/short-term/",
                "domain": DEFAULT_DOMAIN,
                "allow_overwrite": True,
            },
        }

    def test_s3(self):
        storage_settings = build(
            {
                **s3_env("MEDIA_STORAGE", "media-bucket"),
                **s3_env("STATIC_STORAGE", "static-bucket"),
                **s3_env("SHORT_TERM_STORAGE", "short-term-bucket"),
            },
        )

        assert storage_settings.storages == {
            DEFAULT_STORAGE_KEY: {
                "BACKEND": S3_BACKEND,
                "OPTIONS": {
                    **s3_options("media-bucket"),
                    "location": "media/",
                    "file_overwrite": False,
                    "object_parameters": {},
                },
            },
            STORAGE_OVERWRITE_KEY: {
                "BACKEND": S3_BACKEND,
                "OPTIONS": {
                    **s3_options("media-bucket"),
                    "location": "media/",
                    "file_overwrite": True,
                    "object_parameters": {},
                },
            },
            STATICFILES_STORAGE_KEY: {
                "BACKEND": S3_BACKEND,
                "OPTIONS": {
                    **s3_options("static-bucket"),
                    "location": "static/",
                    "file_overwrite": True,
                    "object_parameters": {},
                },
            },
            SHORT_TERM_STORAGE_KEY: {
                "BACKEND": S3_BACKEND,
                "OPTIONS": {
                    **s3_options("short-term-bucket"),
                    "location": "short-term/",
                    "file_overwrite": True,
                    "object_parameters": {},
                },
            },
        }
        assert get_s3_endpoint_url(storage_settings.storages) == "http://minio:9000"

    def test_short_term_disabled_with_backend(self):
        storage_settings = build(
            {
                "SHORT_TERM_STORAGE_ENABLED": "false",
                "SHORT_TERM_STORAGE_BACKEND": "filesystem",
                "SHORT_TERM_STORAGE_FS_ROOT": "/data/short-term",
            },
        )

        assert storage_settings.short_term_enabled is False
        # Defined, so existing short_term_file values still resolve
        assert storage_settings.storages[SHORT_TERM_STORAGE_KEY]["OPTIONS"]["location"] == "/data/short-term"

        with self.assertRaisesMessage(ImproperlyConfigured, "SHORT_TERM_STORAGE_S3_BUCKET_NAME is required"):
            build({"SHORT_TERM_STORAGE_ENABLED": "false", "SHORT_TERM_STORAGE_BACKEND": "s3"})

    def test_s3_optional_values(self):
        storage_settings = build(
            {
                "MEDIA_STORAGE_BACKEND": "S3",
                "MEDIA_STORAGE_S3_BUCKET_NAME": "media-bucket",
                "SHORT_TERM_STORAGE_ENABLED": "false",
            },
        )

        assert storage_settings.storages[DEFAULT_STORAGE_KEY]["OPTIONS"] == {
            "endpoint_url": None,
            "access_key": None,
            "secret_key": None,
            "region_name": None,
            "bucket_name": "media-bucket",
            "querystring_auth": False,
            "location": "media/",
            "file_overwrite": False,
            "object_parameters": {},
        }
        assert get_s3_endpoint_url(storage_settings.storages) is None

    def test_gcs_with_emulator(self):
        storage_settings = build(
            {
                "MEDIA_STORAGE_BACKEND": "gcs",
                "MEDIA_STORAGE_GCS_BUCKET_NAME": "media-bucket",
                "MEDIA_STORAGE_GCS_API_ENDPOINT": "http://fake-gcs:4443",
                "MEDIA_STORAGE_GCS_PUBLIC_ENDPOINT": "http://fake-gcs.example.org/media-bucket",
                "STATIC_STORAGE_BACKEND": "gcs",
                "STATIC_STORAGE_GCS_BUCKET_NAME": "static-bucket",
                "STATIC_STORAGE_GCS_API_ENDPOINT": "http://fake-gcs:4443",
                "SHORT_TERM_STORAGE_BACKEND": "gcs",
                "SHORT_TERM_STORAGE_GCS_BUCKET_NAME": "media-bucket",
                "SHORT_TERM_STORAGE_GCS_API_ENDPOINT": "http://fake-gcs:4443",
            },
        )
        storages_ = storage_settings.storages

        for key in [DEFAULT_STORAGE_KEY, STORAGE_OVERWRITE_KEY, STATICFILES_STORAGE_KEY, SHORT_TERM_STORAGE_KEY]:
            assert storages_[key]["BACKEND"] == GCS_BACKEND
            assert isinstance(storages_[key]["OPTIONS"].pop("credentials"), AnonymousCredentials)

        assert storages_[DEFAULT_STORAGE_KEY]["OPTIONS"] == {
            "bucket_name": "media-bucket",
            "api_endpoint": "http://fake-gcs:4443",
            "custom_endpoint": "http://fake-gcs.example.org/media-bucket",
            "querystring_auth": False,
            "default_acl": None,
            "location": "media/",
            "file_overwrite": False,
            "object_parameters": {},
        }
        assert storages_[STORAGE_OVERWRITE_KEY]["OPTIONS"]["file_overwrite"] is True
        assert storages_[STATICFILES_STORAGE_KEY]["OPTIONS"] == {
            "bucket_name": "static-bucket",
            "api_endpoint": "http://fake-gcs:4443",
            "custom_endpoint": None,
            "querystring_auth": False,
            "default_acl": None,
            "location": "static/",
            "file_overwrite": True,
            "object_parameters": {},
        }
        assert storages_[SHORT_TERM_STORAGE_KEY]["OPTIONS"] == {
            "bucket_name": "media-bucket",
            "api_endpoint": "http://fake-gcs:4443",
            "custom_endpoint": None,
            "querystring_auth": False,
            "default_acl": None,
            "location": "short-term/",
            "file_overwrite": True,
            "object_parameters": {},
        }

    def test_gcs_credentials(self):
        storage_settings = build(
            {
                "MEDIA_STORAGE_BACKEND": "gcs",
                "MEDIA_STORAGE_GCS_BUCKET_NAME": "media-bucket",
                "MEDIA_STORAGE_GCS_CREDENTIALS_B64_GZ": fake_service_account_b64_gz(),
                # Credentials win over the anonymous emulator credentials
                "MEDIA_STORAGE_GCS_API_ENDPOINT": "http://fake-gcs:4443",
                "STATIC_STORAGE_BACKEND": "gcs",
                "STATIC_STORAGE_GCS_BUCKET_NAME": "static-bucket",
                "SHORT_TERM_STORAGE_ENABLED": "false",
            },
        )

        credentials = storage_settings.storages[DEFAULT_STORAGE_KEY]["OPTIONS"]["credentials"]
        assert isinstance(credentials, Credentials)
        assert credentials.service_account_email == "storage@fake-project.iam.gserviceaccount.com"
        assert credentials.project_id == "fake-project"
        # No credentials and no emulator: Application Default Credentials
        assert storage_settings.storages[STATICFILES_STORAGE_KEY]["OPTIONS"]["credentials"] is None

    def test_gcs_invalid_credentials(self):
        with self.assertRaisesMessage(ImproperlyConfigured, "MEDIA_STORAGE_GCS_CREDENTIALS_B64_GZ is invalid"):
            build(
                {
                    "MEDIA_STORAGE_BACKEND": "gcs",
                    "MEDIA_STORAGE_GCS_BUCKET_NAME": "media-bucket",
                    "MEDIA_STORAGE_GCS_CREDENTIALS_B64_GZ": "not-valid",
                    "SHORT_TERM_STORAGE_ENABLED": "false",
                },
            )

    def test_missing_config(self):
        for environ_, message in [
            # Short-term is enabled by default and has no default backend
            ({}, "SHORT_TERM_STORAGE_BACKEND is required"),
            ({"SHORT_TERM_STORAGE_ENABLED": "true"}, "SHORT_TERM_STORAGE_BACKEND is required"),
            (
                {"SHORT_TERM_STORAGE_BACKEND": "s3"},
                "SHORT_TERM_STORAGE_S3_BUCKET_NAME is required",
            ),
            (
                {"SHORT_TERM_STORAGE_BACKEND": "gcs"},
                "SHORT_TERM_STORAGE_GCS_BUCKET_NAME is required",
            ),
            (
                {"MEDIA_STORAGE_BACKEND": "s3", "SHORT_TERM_STORAGE_ENABLED": "false"},
                "MEDIA_STORAGE_S3_BUCKET_NAME is required",
            ),
            (
                {"STATIC_STORAGE_BACKEND": "gcs", "SHORT_TERM_STORAGE_ENABLED": "false"},
                "STATIC_STORAGE_GCS_BUCKET_NAME is required",
            ),
            (
                {"MEDIA_STORAGE_BACKEND": "azure", "SHORT_TERM_STORAGE_ENABLED": "false"},
                "MEDIA_STORAGE_BACKEND should be one of filesystem|s3|gcs, got 'azure'",
            ),
        ]:
            with self.subTest(environ_=environ_), self.assertRaisesMessage(ImproperlyConfigured, message):
                build(environ_)


class TestGoogleCloudStorage(SimpleTestCase):
    def test_api_endpoint_and_public_url(self):
        storage = GoogleCloudStorage(
            bucket_name="media-bucket",
            credentials=AnonymousCredentials(),
            api_endpoint="http://fake-gcs:4443",
            custom_endpoint="http://fake-gcs.example.org/media-bucket",
            querystring_auth=False,
            default_acl=None,
            location="short-term/",
        )

        assert storage.client.api_endpoint == "http://fake-gcs:4443"
        assert (
            storage.url("project/1/export.csv") == "http://fake-gcs.example.org/media-bucket/short-term/project/1/export.csv"
        )


class TestObjectParameters(SimpleTestCase):
    EXPORT_NAME = "media/project/1/asset/export/01J/results_1.csv.gz"
    INPUT_NAME = "media/project/1/asset/input/01J/image.png"

    def get_storage(self, config: dict[str, typing.Any]):
        return import_string(config["BACKEND"])(**config["OPTIONS"])

    def test_object_parameters(self):
        for backend, environ_, content_disposition_key in [
            (
                "s3",
                {
                    "MEDIA_STORAGE_S3_BUCKET_NAME": "media-bucket",
                    "SHORT_TERM_STORAGE_S3_BUCKET_NAME": "short-term-bucket",
                },
                "ContentDisposition",
            ),
            (
                "gcs",
                {
                    "MEDIA_STORAGE_GCS_BUCKET_NAME": "media-bucket",
                    "MEDIA_STORAGE_GCS_API_ENDPOINT": "http://fake-gcs:4443",
                    "SHORT_TERM_STORAGE_GCS_BUCKET_NAME": "short-term-bucket",
                    "SHORT_TERM_STORAGE_GCS_API_ENDPOINT": "http://fake-gcs:4443",
                },
                "content_disposition",
            ),
        ]:
            with self.subTest(backend=backend):
                storages_ = build(
                    {
                        "MEDIA_STORAGE_BACKEND": backend,
                        "SHORT_TERM_STORAGE_ENABLED": "true",
                        "SHORT_TERM_STORAGE_BACKEND": backend,
                        **environ_,
                    },
                ).storages
                attachment = {content_disposition_key: "attachment"}
                # Only exports are attachments
                for key in [DEFAULT_STORAGE_KEY, STORAGE_OVERWRITE_KEY, SHORT_TERM_STORAGE_KEY]:
                    storage = self.get_storage(storages_[key])
                    assert storage.get_object_parameters(self.EXPORT_NAME) == attachment
                    assert storage.get_object_parameters(self.INPUT_NAME) == {}


TEST_STORAGES = {
    DEFAULT_STORAGE_KEY: {"BACKEND": FILESYSTEM_BACKEND, "OPTIONS": {"location": "/tmp/media"}},  # noqa: S108
    STORAGE_OVERWRITE_KEY: {
        "BACKEND": FILESYSTEM_BACKEND,
        "OPTIONS": {"location": "/tmp/media", "allow_overwrite": True},  # noqa: S108
    },
    STATICFILES_STORAGE_KEY: {"BACKEND": STATICFILES_FILESYSTEM_BACKEND},
    SHORT_TERM_STORAGE_KEY: {
        "BACKEND": FILESYSTEM_BACKEND,
        "OPTIONS": {
            "location": "/tmp/short-term",  # noqa: S108
            "base_url": "/short-term/",
            "domain": "https://short-term.example.org",
            "allow_overwrite": True,
        },
    },
}


def storage_location(field: OverwritableFileField) -> str:
    return str(typing.cast("FileSystemStorage", field.storage).location)


def with_short_term(config: dict[str, typing.Any]):
    return {**TEST_STORAGES, SHORT_TERM_STORAGE_KEY: config}


class TestShortTermStorageCheck(SimpleTestCase):
    @override_settings(
        SHORT_TERM_STORAGE_ENABLED=False,
        STORAGES={key: value for key, value in TEST_STORAGES.items() if key != SHORT_TERM_STORAGE_KEY},
    )
    def test_disabled_without_short_term_storage(self):
        assert short_term_storage_check(None) == []

    @override_settings(SHORT_TERM_STORAGE_ENABLED=False, STORAGES=with_short_term(TEST_STORAGES[DEFAULT_STORAGE_KEY]))
    def test_disabled_with_same_target(self):
        # The short-term storage is still used to read existing short_term_file values
        errors = short_term_storage_check(None)
        assert len(errors) == 1
        assert "write to the same place" in errors[0].msg

    @override_settings(SHORT_TERM_STORAGE_ENABLED=True, STORAGES=TEST_STORAGES)
    def test_separate_filesystem(self):
        assert short_term_storage_check(None) == []

    @override_settings(
        SHORT_TERM_STORAGE_ENABLED=True,
        STORAGES={key: value for key, value in TEST_STORAGES.items() if key != SHORT_TERM_STORAGE_KEY},
    )
    def test_missing_short_term_storage(self):
        errors = short_term_storage_check(None)
        assert len(errors) == 1
        assert "is not defined" in errors[0].msg

    def test_same_target(self):
        s3_media = build({**s3_env("MEDIA_STORAGE", "bucket"), "SHORT_TERM_STORAGE_ENABLED": "false"}).storages[
            DEFAULT_STORAGE_KEY
        ]
        gcs_media = build(
            {
                "MEDIA_STORAGE_BACKEND": "gcs",
                "MEDIA_STORAGE_GCS_BUCKET_NAME": "bucket",
                "MEDIA_STORAGE_GCS_API_ENDPOINT": "http://fake-gcs:4443",
                "SHORT_TERM_STORAGE_ENABLED": "false",
            },
        ).storages[DEFAULT_STORAGE_KEY]

        for name, long_term, short_term, has_error in [
            (
                "Same filesystem root",
                TEST_STORAGES[DEFAULT_STORAGE_KEY],
                {"BACKEND": FILESYSTEM_BACKEND, "OPTIONS": {"location": "/tmp/media/"}},  # noqa: S108
                True,
            ),
            (
                "Filesystem root from MEDIA_ROOT",
                {"BACKEND": FILESYSTEM_BACKEND},
                {"BACKEND": FILESYSTEM_BACKEND, "OPTIONS": {"location": "/tmp/media-root"}},  # noqa: S108
                True,
            ),
            (
                "Same S3 bucket and location",
                s3_media,
                {**s3_media, "OPTIONS": {**s3_media["OPTIONS"], "location": "/media"}},
                True,
            ),
            (
                "Same S3 bucket, other location",
                s3_media,
                {**s3_media, "OPTIONS": {**s3_media["OPTIONS"], "location": "short-term/"}},
                False,
            ),
            (
                "Same S3 location, other endpoint",
                s3_media,
                {**s3_media, "OPTIONS": {**s3_media["OPTIONS"], "endpoint_url": "http://other-minio:9000"}},
                False,
            ),
            (
                "Same GCS bucket and location",
                gcs_media,
                {**gcs_media, "OPTIONS": {**gcs_media["OPTIONS"], "file_overwrite": True}},
                True,
            ),
            (
                "Same GCS bucket, other location",
                gcs_media,
                {**gcs_media, "OPTIONS": {**gcs_media["OPTIONS"], "location": "short-term/"}},
                False,
            ),
        ]:
            storages_ = {**TEST_STORAGES, DEFAULT_STORAGE_KEY: long_term, SHORT_TERM_STORAGE_KEY: short_term}
            with (
                self.subTest(name),
                override_settings(SHORT_TERM_STORAGE_ENABLED=True, STORAGES=storages_, MEDIA_ROOT="/tmp/media-root"),  # noqa: S108
            ):
                errors = short_term_storage_check(None)
                assert bool(errors) == has_error, errors


class TestLazyStorage(SimpleTestCase):
    def test_override_settings_reaches_field_storage(self):
        field = ProjectAsset._meta.get_field("file")
        assert isinstance(field, OverwritableFileField)

        with override_settings(STORAGES=TEST_STORAGES):
            assert storage_location(field) == "/tmp/media"  # noqa: S108
            assert field.storage == storages[STORAGE_OVERWRITE_KEY]

        other_storages = {
            **TEST_STORAGES,
            STORAGE_OVERWRITE_KEY: {"BACKEND": FILESYSTEM_BACKEND, "OPTIONS": {"location": "/tmp/other-media"}},  # noqa: S108
        }
        with override_settings(STORAGES=other_storages):
            assert storage_location(field) == "/tmp/other-media"  # noqa: S108

    def test_storage_key(self):
        missing_short_term_storages = {key: value for key, value in TEST_STORAGES.items() if key != SHORT_TERM_STORAGE_KEY}
        with override_settings(STORAGES=missing_short_term_storages):
            # Storage is not resolved on field creation
            field = ShortTermFileField()

        with override_settings(STORAGES=TEST_STORAGES):
            assert storage_location(field) == "/tmp/short-term"  # noqa: S108

    def test_deconstruct_drops_storage(self):
        field = ShortTermFileField(upload_to="test/")
        _, _, _, kwargs = field.deconstruct()
        assert "storage" not in kwargs

        explicit_storage = storages[DEFAULT_STORAGE_KEY]
        field = OverwritableFileField(storage=explicit_storage)
        _, _, _, kwargs = field.deconstruct()
        assert kwargs["storage"] is explicit_storage

    def test_explicit_storage(self):
        lazy_storages_count = len(_lazy_storages)
        explicit_storage = storages[DEFAULT_STORAGE_KEY]
        field = OverwritableFileField(storage=explicit_storage)
        assert field.storage is explicit_storage
        assert field.lazy_storage is None
        assert field.has_storage()
        assert len(_lazy_storages) == lazy_storages_count

    def test_lazy_storages_are_pruned(self):
        lazy_storages_count = len(_lazy_storages)
        field = ShortTermFileField()
        assert len(_lazy_storages) == lazy_storages_count + 1
        del field
        gc.collect()
        assert len(_lazy_storages) == lazy_storages_count


class TestGetAbsoluteUri(SimpleTestCase):
    def get_field_file(self, field: OverwritableFileField, name: str):
        return FieldFile(instance=ProjectAsset(), field=field, name=name)

    @override_settings(STORAGES=TEST_STORAGES)
    def test_filesystem(self):
        media_domain = Config.MEDIA_STORAGE_DOMAIN.geturl()
        # Without domain option: MEDIA_STORAGE_DOMAIN
        file = self.get_field_file(OverwritableFileField(), "project/1/image.png")
        assert get_absolute_uri(file) == f"{media_domain}/media/project/1/image.png"

        file = self.get_field_file(ShortTermFileField(), "project/1/export.csv")
        assert get_absolute_uri(file) == "https://short-term.example.org/short-term/project/1/export.csv"

        assert get_absolute_uri(None) is None
        assert get_absolute_uri(self.get_field_file(ShortTermFileField(), "")) is None

    def test_gcs(self):
        gcs_storages = with_short_term(
            {
                "BACKEND": GCS_BACKEND,
                "OPTIONS": {
                    "bucket_name": "bucket",
                    "credentials": AnonymousCredentials(),
                    "api_endpoint": "http://fake-gcs:4443",
                    "custom_endpoint": "http://fake-gcs.example.org/bucket",
                    "querystring_auth": False,
                    "location": "short-term/",
                },
            },
        )
        with override_settings(STORAGES=gcs_storages):
            file = self.get_field_file(ShortTermFileField(), "project/1/export.csv")
            assert get_absolute_uri(file) == "http://fake-gcs.example.org/bucket/short-term/project/1/export.csv"


class TestCurrentFile(SimpleTestCase):
    def test_missing_short_term_storage(self):
        project_asset = ProjectAsset(short_term_file="project/1/asset/export/01J/results.csv")

        with override_settings(STORAGES=TEST_STORAGES):
            assert project_asset.current_file == project_asset.short_term_file

        missing_short_term_storages = {key: value for key, value in TEST_STORAGES.items() if key != SHORT_TERM_STORAGE_KEY}
        with (
            override_settings(STORAGES=missing_short_term_storages),
            self.assertLogs("apps.project.models", level="WARNING") as logs,
        ):
            assert not project_asset.current_file
        assert "is not defined" in logs.output[0]

        # The long-term file wins without resolving the short-term storage
        project_asset.file = "project/1/asset/export/01J/results.csv"
        with override_settings(STORAGES=missing_short_term_storages):
            assert project_asset.current_file == project_asset.file

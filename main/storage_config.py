"""Build Django STORAGES from environment variables.

Each storage tier reads variables with its own prefix:
- MEDIA_STORAGE_*: long-term media (`default`, `default-overwrite`)
- STATIC_STORAGE_*: static files (`staticfiles`)
- SHORT_TERM_STORAGE_*: short-term files (`short-term`), when SHORT_TERM_STORAGE_ENABLED or SHORT_TERM_STORAGE_BACKEND
    is set. SHORT_TERM_STORAGE_ENABLED selects whether exports are written to the short-term storage, promoted and cleaned.
    With SHORT_TERM_STORAGE_ENABLED=false, a configured backend keeps existing short-term files readable.

<PREFIX>_BACKEND selects the backend:
- filesystem: <PREFIX>_FS_ROOT, <PREFIX>_FS_URL, <PREFIX>_FS_DOMAIN (not used by static)
- s3: <PREFIX>_S3_BUCKET_NAME, <PREFIX>_S3_ENDPOINT_URL, <PREFIX>_S3_ACCESS_KEY_ID,
    <PREFIX>_S3_SECRET_ACCESS_KEY, <PREFIX>_S3_REGION_NAME
- gcs: <PREFIX>_GCS_BUCKET_NAME, <PREFIX>_GCS_CREDENTIALS_B64_GZ (gzip -cn sa.json | base64 -w 0),
    <PREFIX>_GCS_API_ENDPOINT (Eg: fake-gcs-server), <PREFIX>_GCS_PUBLIC_ENDPOINT (public URL base, including the bucket)

Weekly promotion of short-term exports (read in main/settings.py, See apps/project/short_term_storage.py):
- SHORT_TERM_STORAGE_PROMOTION_COOLDOWN_DAYS (default 7): days without export changes before promotion
- SHORT_TERM_STORAGE_TTL_DAYS (default 7): days after promotion before the short-term copy is deleted
"""

import enum
import typing
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import environ  # type: ignore[reportMissingTypeStubs]
from django.core.exceptions import ImproperlyConfigured

from utils.common import parse_b64gzjson_to_dict

DEFAULT_STORAGE_KEY = "default"
STORAGE_OVERWRITE_KEY = "default-overwrite"
STATICFILES_STORAGE_KEY = "staticfiles"
SHORT_TERM_STORAGE_KEY = "short-term"

FILESYSTEM_BACKEND = "main.storage_backends.FileSystemStorage"
STATICFILES_FILESYSTEM_BACKEND = "django.contrib.staticfiles.storage.StaticFilesStorage"
S3_BACKEND = "main.storage_backends.S3Storage"
GCS_BACKEND = "main.storage_backends.GoogleCloudStorage"

StorageConfig = dict[str, typing.Any]


class StorageBackendType(enum.StrEnum):
    FILESYSTEM = "filesystem"
    S3 = "s3"
    GCS = "gcs"


class _TierEnv:
    def __init__(self, environ_: Mapping[str, str], prefix: str):
        self.environ = environ_
        self.prefix = prefix

    def key(self, name: str) -> str:
        return f"{self.prefix}_{name}"

    @typing.overload
    def get(self, name: str, default: str) -> str: ...

    @typing.overload
    def get(self, name: str, default: None = None) -> str | None: ...

    def get(self, name: str, default: str | None = None) -> str | None:
        return self.environ.get(self.key(name)) or default

    def require(self, name: str) -> str:
        value = self.get(name)
        if value is None:
            raise ImproperlyConfigured(f"{self.key(name)} is required")
        return value

    def backend(self, default: StorageBackendType | None = None) -> StorageBackendType:
        value = self.get("BACKEND") or default
        if value is None:
            raise ImproperlyConfigured(f"{self.key('BACKEND')} is required")
        try:
            return StorageBackendType(value.lower())
        except ValueError:
            choices = "|".join(StorageBackendType)
            raise ImproperlyConfigured(f"{self.key('BACKEND')} should be one of {choices}, got {value!r}") from None


def _s3_options(tier_env: _TierEnv) -> StorageConfig:
    return {
        "endpoint_url": tier_env.get("S3_ENDPOINT_URL"),
        "access_key": tier_env.get("S3_ACCESS_KEY_ID"),
        "secret_key": tier_env.get("S3_SECRET_ACCESS_KEY"),
        "region_name": tier_env.get("S3_REGION_NAME"),
        "bucket_name": tier_env.require("S3_BUCKET_NAME"),
        "querystring_auth": False,
    }


def _gcs_credentials(tier_env: _TierEnv, api_endpoint: str | None):
    from google.auth.credentials import AnonymousCredentials  # noqa: PLC0415
    from google.oauth2.service_account import Credentials  # noqa: PLC0415

    credentials_b64_gz = tier_env.get("GCS_CREDENTIALS_B64_GZ")
    if credentials_b64_gz:
        try:
            return Credentials.from_service_account_info(parse_b64gzjson_to_dict(credentials_b64_gz))
        except Exception as e:
            raise ImproperlyConfigured(f"{tier_env.key('GCS_CREDENTIALS_B64_GZ')} is invalid: {e}") from e
    if api_endpoint:
        return AnonymousCredentials()
    # Application Default Credentials
    return None


def _gcs_options(tier_env: _TierEnv) -> StorageConfig:
    api_endpoint = tier_env.get("GCS_API_ENDPOINT")
    return {
        "bucket_name": tier_env.require("GCS_BUCKET_NAME"),
        "credentials": _gcs_credentials(tier_env, api_endpoint),
        "api_endpoint": api_endpoint,
        "custom_endpoint": tier_env.get("GCS_PUBLIC_ENDPOINT"),
        "querystring_auth": False,
        # Uniform bucket-level access: object ACLs are not allowed
        "default_acl": None,
    }


def _object_storage(
    tier_env: _TierEnv,
    backend: StorageBackendType,
    *,
    location: str,
    file_overwrite: bool,
) -> StorageConfig:
    # Exports are served as attachments by the backends (See main.storage_backends)
    if backend == StorageBackendType.S3:
        return {
            "BACKEND": S3_BACKEND,
            "OPTIONS": {
                **_s3_options(tier_env),
                "location": location,
                "file_overwrite": file_overwrite,
                "object_parameters": {},
            },
        }
    if backend == StorageBackendType.GCS:
        return {
            "BACKEND": GCS_BACKEND,
            "OPTIONS": {
                **_gcs_options(tier_env),
                "location": location,
                "file_overwrite": file_overwrite,
                "object_parameters": {},
            },
        }
    raise NotImplementedError(backend)


def _overwrite_variant(config: StorageConfig) -> StorageConfig:
    options = config.get("OPTIONS", {})
    if config["BACKEND"] == FILESYSTEM_BACKEND:
        return {**config, "OPTIONS": {**options, "allow_overwrite": True}}
    return {**config, "OPTIONS": {**options, "file_overwrite": True}}


@dataclass(frozen=True)
class StorageSettings:
    storages: dict[str, StorageConfig]
    media_root: str
    media_url: str
    media_domain: str
    static_root: str
    static_url: str
    short_term_enabled: bool


def build_storage_settings(
    environ_: Mapping[str, str],
    *,
    base_dir: Path,
    default_domain: str,
) -> StorageSettings:
    """Build STORAGES and related settings from environment variables."""
    storages: dict[str, StorageConfig] = {}

    # Long-term media
    media_env = _TierEnv(environ_, "MEDIA_STORAGE")
    media_backend = media_env.backend(default=StorageBackendType.FILESYSTEM)
    media_root = media_env.get("FS_ROOT", str(base_dir / ".data/media"))
    media_url = media_env.get("FS_URL", "media/")
    media_domain = media_env.get("FS_DOMAIN", default_domain)
    if media_backend == StorageBackendType.FILESYSTEM:
        # location and base_url are read from MEDIA_ROOT and MEDIA_URL
        storages[DEFAULT_STORAGE_KEY] = {
            "BACKEND": FILESYSTEM_BACKEND,
            "OPTIONS": {"domain": media_domain.rstrip("/")},
        }
    else:
        storages[DEFAULT_STORAGE_KEY] = _object_storage(media_env, media_backend, location="media/", file_overwrite=False)
    storages[STORAGE_OVERWRITE_KEY] = _overwrite_variant(storages[DEFAULT_STORAGE_KEY])

    # Static
    static_env = _TierEnv(environ_, "STATIC_STORAGE")
    static_backend = static_env.backend(default=StorageBackendType.FILESYSTEM)
    static_root = static_env.get("FS_ROOT", str(base_dir / ".data/static"))
    static_url = static_env.get("FS_URL", "static/")
    if static_backend == StorageBackendType.FILESYSTEM:
        # location and base_url are read from STATIC_ROOT and STATIC_URL
        storages[STATICFILES_STORAGE_KEY] = {"BACKEND": STATICFILES_FILESYSTEM_BACKEND}
    else:
        storages[STATICFILES_STORAGE_KEY] = _object_storage(
            static_env,
            static_backend,
            location="static/",
            file_overwrite=True,
        )

    # Short-term
    short_term_enabled = environ.Env.parse_value(environ_.get("SHORT_TERM_STORAGE_ENABLED", "true"), bool)
    short_term_env = _TierEnv(environ_, "SHORT_TERM_STORAGE")
    # Defined while disabled too if configured, so existing short_term_file values still resolve
    if short_term_enabled or short_term_env.get("BACKEND"):
        short_term_backend = short_term_env.backend()
        if short_term_backend == StorageBackendType.FILESYSTEM:
            short_term_domain = short_term_env.get("FS_DOMAIN", default_domain)
            storages[SHORT_TERM_STORAGE_KEY] = {
                "BACKEND": FILESYSTEM_BACKEND,
                "OPTIONS": {
                    "location": short_term_env.get("FS_ROOT", str(base_dir / ".data/short-term")),
                    "base_url": short_term_env.get("FS_URL", "/short-term/"),
                    "domain": short_term_domain.rstrip("/"),
                    "allow_overwrite": True,
                },
            }
        else:
            storages[SHORT_TERM_STORAGE_KEY] = _object_storage(
                short_term_env,
                short_term_backend,
                location="short-term/",
                file_overwrite=True,
            )

    return StorageSettings(
        storages=storages,
        media_root=media_root,
        media_url=media_url,
        media_domain=media_domain.rstrip("/"),
        static_root=static_root,
        static_url=static_url,
        short_term_enabled=short_term_enabled,
    )


def get_s3_endpoint_url(storages: Mapping[str, StorageConfig]) -> str | None:
    """Return the first S3 endpoint url used by STORAGES."""
    for config in storages.values():
        if config["BACKEND"] == S3_BACKEND and (endpoint_url := config["OPTIONS"].get("endpoint_url")):
            return endpoint_url
    return None


def get_storage_target(config: StorageConfig, *, media_root: str) -> tuple[str | None, ...]:
    """Return a value which is equal for storage configs which write to the same place."""
    backend = config["BACKEND"]
    options = config.get("OPTIONS", {})
    location = (options.get("location") or "").strip("/")
    if backend == S3_BACKEND:
        return ("s3", options.get("endpoint_url"), options.get("bucket_name"), location)
    if backend == GCS_BACKEND:
        return ("gcs", options.get("api_endpoint"), options.get("bucket_name"), location)
    # Filesystem
    return ("filesystem", str(Path(options.get("location") or media_root).resolve()))

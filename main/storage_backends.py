# pyright: reportMissingTypeStubs=false
import typing

from django.core.files.storage import FileSystemStorage as DjangoFileSystemStorage
from django.utils.deconstruct import deconstructible
from google.cloud.storage import Client
from storages.backends.gcloud import GoogleCloudStorage as BaseGoogleCloudStorage
from storages.backends.s3boto3 import S3Boto3Storage

# Project export assets (See apps.project.models.UploadHelper.project_asset)
EXPORT_KEY_PART = "/asset/export/"


def is_export_name(name: str) -> bool:
    return EXPORT_KEY_PART in name


@deconstructible
class FileSystemStorage(DjangoFileSystemStorage):
    """FileSystemStorage which knows the domain its files are served from."""

    def __init__(self, *args: typing.Any, domain: str | None = None, **kwargs: typing.Any):
        super().__init__(*args, **kwargs)
        self.domain = domain


@deconstructible
class S3Storage(S3Boto3Storage):
    """S3Boto3Storage which serves exports as attachments."""

    @typing.override
    def get_object_parameters(self, name: str) -> dict[str, typing.Any]:
        object_parameters = super().get_object_parameters(name)
        if is_export_name(name):
            object_parameters.setdefault("ContentDisposition", "attachment")
        return object_parameters


@deconstructible
class GoogleCloudStorage(BaseGoogleCloudStorage):
    """GoogleCloudStorage with a configurable API endpoint (Eg: fake-gcs-server), which serves exports as attachments."""

    api_endpoint: str | None  # type: ignore[reportUninitializedInstanceVariable]
    _client: Client | None

    @typing.override
    def get_default_settings(self):
        return {
            **super().get_default_settings(),
            "api_endpoint": None,
        }

    @property
    @typing.override
    def client(self):
        if self._client is None:
            self._client = Client(
                project=self.project_id,
                credentials=self.credentials,
                client_options={"api_endpoint": self.api_endpoint} if self.api_endpoint else None,
            )
        return self._client

    @typing.override
    def get_object_parameters(self, name: str) -> dict[str, typing.Any]:
        object_parameters = super().get_object_parameters(name)
        if is_export_name(name):
            object_parameters.setdefault("content_disposition", "attachment")
        return object_parameters

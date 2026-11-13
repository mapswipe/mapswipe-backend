import logging
import typing

from firebase_admin.db import Reference as FbReference  # type: ignore[reportMissingTypeStubs]
from pyfirebase_mapswipe import models as firebase_models
from pyfirebase_mapswipe import utils as firebase_utils

from apps.common.firebase.base import FirebasePush
from apps.common.models import Announcement, AppInfo
from main.config import Config

logger = logging.getLogger(__name__)


class FirebaseAnnouncementPush(FirebasePush[Announcement, firebase_models.FbAnnouncement]):
    model_class = Announcement
    firebase_model_class = firebase_models.FbAnnouncement

    @typing.override
    def allow_delete_object_on_firebase(self) -> bool:
        return True

    @typing.override
    def handle_new_object_on_firebase(self, model_obj: Announcement, fb_reference: FbReference):
        announcement_data = firebase_models.FbAnnouncement(
            text=model_obj.text,
            url=model_obj.url,
        )
        fb_reference.set(
            value=firebase_utils.serialize(announcement_data),
        )

    @typing.override
    def handle_object_update_on_firebase(
        self,
        model_obj: Announcement,
        fb_obj: firebase_models.FbAnnouncement,
        fb_reference: FbReference,
    ):
        fb_reference.update(
            value=firebase_utils.serialize(
                firebase_models.FbAnnouncement(
                    text=model_obj.text,
                    url=model_obj.url,
                ),
            ),
        )

    @typing.override
    def get_firebase_path(self, firebase_id: str, model=Announcement):  # type: ignore[reportMissingParameterType]
        return Config.FirebaseKeys.announcement()


class FirebaseAppInfoPush(FirebasePush[AppInfo, firebase_models.FbAppInfo]):
    model_class = AppInfo
    firebase_model_class = firebase_models.FbAppInfo

    def _get_firebase_data(self, model_obj: AppInfo) -> firebase_models.FbAppInfo:
        latest_version = model_obj.latest_version
        # NOTE: Releases newer than the latest version are drafts and are not published
        releases = model_obj.get_published_releases()
        return firebase_models.FbAppInfo(
            minSupportedVersion=model_obj.min_supported_version,
            latestVersion=latest_version.version if latest_version else firebase_models.UNDEFINED,
            releases={
                release.firebase_key: firebase_models.FbAppInfoRelease(
                    version=release.version,
                    versionCode=release.version_code,
                    updates=release.updates or firebase_models.UNDEFINED,
                    incompatibleChanges=release.incompatible_changes or firebase_models.UNDEFINED,
                )
                for release in releases
            }
            or firebase_models.UNDEFINED,
        )

    # NOTE: We always overwrite the whole node so that removed releases are also removed from firebase
    @typing.override
    def handle_new_object_on_firebase(self, model_obj: AppInfo, fb_reference: FbReference):
        fb_reference.set(
            value=firebase_utils.serialize(self._get_firebase_data(model_obj)),
        )

    @typing.override
    def handle_object_update_on_firebase(
        self,
        model_obj: AppInfo,
        fb_obj: firebase_models.FbAppInfo,
        fb_reference: FbReference,
    ):
        fb_reference.set(
            value=firebase_utils.serialize(self._get_firebase_data(model_obj)),
        )

    @typing.override
    def get_firebase_path(self, firebase_id: str, model=AppInfo):  # type: ignore[reportMissingParameterType]
        return Config.FirebaseKeys.app_info(str(self.obj.platform_enum.label))

import logging
import typing

from firebase_admin.db import Reference as FbReference
from pyfirebase_mapswipe import models as firebase_models
from pyfirebase_mapswipe import utils as firebase_utils

from apps.common.firebase.base import FirebasePush
from apps.common.models import Announcement
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
    def get_firebase_path(self, firebase_id: str, model=Announcement):
        return Config.FirebaseKeys.announcement()

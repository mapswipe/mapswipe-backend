import logging
import typing

from firebase_admin.db import Reference as FbReference
from pyfirebase_mapswipe import models as firebase_models
from pyfirebase_mapswipe import utils as firebase_utils

from apps.common.firebase import FirebasePush
from apps.project.models import Organization
from main.celery import app
from main.config import Config

logger = logging.getLogger(__name__)


class FirebaseOrganization(FirebasePush[Organization]):
    model_obj: Organization
    model = Organization

    @typing.override
    def handle_new_object_on_firebase(self, model_obj: Organization, fb_reference: FbReference):
        organization_data = firebase_models.FbOrganisation(
            name=model_obj.name,
            nameKey="",
            description=model_obj.description or firebase_models.UNDEFINED,
            abbreviation=model_obj.abbreviation or firebase_models.UNDEFINED,
            isArchived=model_obj.is_archived,
        )

        fb_reference.set(
            value={
                **firebase_utils.serialize(organization_data),
            },
        )

    @typing.override
    def handle_object_update_on_firebase(self, model_obj: Organization, fb_reference: FbReference):
        fb_reference.update(
            value=firebase_utils.serialize(
                firebase_models.FbOrganisation(
                    name=model_obj.name,
                    nameKey="",
                    description=model_obj.description or firebase_models.UNDEFINED,
                    abbreviation=model_obj.abbreviation or firebase_models.UNDEFINED,
                    isArchived=model_obj.is_archived,
                ),
            ),
        )

    @typing.override
    def get_firebase_path(self, canonical_id: str, model=Organization):
        return Config.FirebaseKeys.organization(canonical_id)

    @staticmethod
    @typing.override
    @app.task()
    def task(obj_id: int) -> None:
        FirebaseOrganization(obj_id).push()

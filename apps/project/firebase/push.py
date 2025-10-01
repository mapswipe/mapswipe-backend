import logging
import typing

from firebase_admin.db import Reference as FbReference  # type: ignore[reportMissingTypeStubs]
from pyfirebase_mapswipe import models as firebase_models
from pyfirebase_mapswipe import utils as firebase_utils

from apps.common.firebase.base import FirebasePush
from apps.project.models import Organization
from main.config import Config

logger = logging.getLogger(__name__)


class FirebaseOrganizationPush(FirebasePush[Organization, firebase_models.FbOrganisation]):
    model_class = Organization
    firebase_model_class = firebase_models.FbOrganisation

    @typing.override
    def handle_new_object_on_firebase(self, model_obj: Organization, fb_reference: FbReference):
        organization_data = firebase_models.FbOrganisation(
            name=model_obj.name,
            nameKey=model_obj.name.lower().strip(),
            description=model_obj.description,
            abbreviation=model_obj.abbreviation,
            isArchived=model_obj.is_archived,
        )
        fb_reference.set(
            value=firebase_utils.serialize(organization_data),
        )

    @typing.override
    def handle_object_update_on_firebase(
        self,
        model_obj: Organization,
        fb_obj: firebase_models.FbOrganisation,
        fb_reference: FbReference,
    ):
        fb_reference.update(
            value=firebase_utils.serialize(
                firebase_models.FbOrganisation(
                    name=model_obj.name,
                    nameKey=model_obj.name.lower().strip(),
                    description=model_obj.description,
                    abbreviation=model_obj.abbreviation,
                    isArchived=model_obj.is_archived,
                ),
            ),
        )

    @typing.override
    def get_firebase_path(self, firebase_id: str, model=Organization):  # type: ignore[reportMissingParameterType]
        return Config.FirebaseKeys.organization(firebase_id)

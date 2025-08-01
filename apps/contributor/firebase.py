import logging
import typing

from celery import shared_task
from firebase_admin.db import Reference as FbReference
from pyfirebase_mapswipe import models as firebase_models
from pyfirebase_mapswipe import utils as firebase_utils

from apps.common.firebase import FirebasePush
from apps.contributor.models import ContributorTeam, ContributorUser
from main.celery import app
from main.config import Config

logger = logging.getLogger(__name__)


class FirebaseContributorTeam(FirebasePush[ContributorTeam]):
    model_obj: ContributorTeam
    model = ContributorTeam

    @typing.override
    def handle_new_object_on_firebase(self, model_obj: ContributorTeam, fb_reference: FbReference):
        contributor_team_data = firebase_models.FbTeam(
            teamName=model_obj.name,
            isArchived=model_obj.is_archived,
            teamToken=str(model_obj.token),
        )

        fb_reference.set(
            value=firebase_utils.serialize(contributor_team_data),
        )

    @typing.override
    def handle_object_update_on_firebase(self, model_obj: ContributorTeam, fb_reference: FbReference):
        fb_reference.update(
            value=firebase_utils.serialize(
                firebase_models.FbTeam(
                    teamName=model_obj.name,
                    isArchived=model_obj.is_archived,
                    teamToken=str(model_obj.token),
                ),
            ),
        )

    @typing.override
    def get_firebase_path(self, firebase_id: str, model=ContributorTeam):
        return Config.FirebaseKeys.contributor_team(firebase_id)

    @staticmethod
    @typing.override
    @app.task()
    def task(obj_id: int) -> None:
        FirebaseContributorTeam(obj_id).push()


class FirebaseContributorUser(FirebasePush[ContributorUser]):
    model_obj: ContributorUser
    model = ContributorUser

    @typing.override
    def handle_new_object_on_firebase(self, model_obj: ContributorUser, fb_reference: FbReference):
        # FIXME(tnagorra): Use a better exception
        raise Exception("User cannot be created from mapswipe-backend")

    @typing.override
    def handle_object_update_on_firebase(self, model_obj: ContributorUser, fb_reference: FbReference):
        fb_reference.update(
            value=firebase_utils.serialize(
                firebase_models.FbUserUpdateInput(
                    teamId=model_obj.team.firebase_id if model_obj.team else firebase_models.UNDEFINED,
                ),
            ),
        )

    @typing.override
    def get_firebase_path(self, firebase_id: str, model=ContributorUser):
        return Config.FirebaseKeys.contributor_user(firebase_id)

    @staticmethod
    @typing.override
    @app.task()
    def task(obj_id: int) -> None: ...


@shared_task
def firebase_contributor_user(obj_id: int):
    FirebaseContributorUser(obj_id).push()

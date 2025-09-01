import logging
import typing

from firebase_admin.db import Reference as FbReference
from pyfirebase_mapswipe import extended_models as firebase_ext_models
from pyfirebase_mapswipe import models as firebase_models
from pyfirebase_mapswipe import utils as firebase_utils

from apps.common.firebase import FirebasePush
from apps.contributor.models import ContributorTeam, ContributorUser, ContributorUserGroup
from main.config import Config

logger = logging.getLogger(__name__)


class FirebaseContributorTeam(FirebasePush[ContributorTeam, firebase_models.FbTeam]):
    model_class = ContributorTeam
    firebase_model_class = firebase_models.FbTeam

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
    def handle_object_update_on_firebase(
        self,
        model_obj: ContributorTeam,
        fb_obj: firebase_models.FbTeam,
        fb_reference: FbReference,
    ):
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


class FirebaseContributorUser(FirebasePush[ContributorUser, firebase_ext_models.FbUser]):
    model_class = ContributorUser
    firebase_model_class = firebase_ext_models.FbUser

    @typing.override
    def handle_new_object_on_firebase(self, model_obj: ContributorUser, fb_reference: FbReference):
        # FIXME(tnagorra): Use a better exception
        raise Exception("User cannot be created from mapswipe-backend")

    @typing.override
    def handle_object_update_on_firebase(
        self,
        model_obj: ContributorUser,
        fb_obj: firebase_ext_models.FbUser,
        fb_reference: FbReference,
    ):
        fb_reference.update(
            value=firebase_utils.serialize(
                firebase_models.FbUserUpdateInput(
                    teamId=model_obj.team.firebase_id if model_obj.team else None,
                ),
            ),
        )

    @typing.override
    def get_firebase_path(self, firebase_id: str, model=ContributorUser):
        return Config.FirebaseKeys.contributor_user(firebase_id)


class FirebaseContributorUserGroup(FirebasePush[ContributorUserGroup, firebase_ext_models.FbUserGroup]):
    model_class = ContributorUserGroup
    firebase_model_class = firebase_ext_models.FbUserGroup

    @typing.override
    def handle_new_object_on_firebase(self, model_obj: ContributorUserGroup, fb_reference: FbReference):
        contributor_user_group_data = firebase_ext_models.FbUserGroup(
            createdAt=int(model_obj.created_at.timestamp()),
            # FIXME: What to use for fallback?
            createdBy=model_obj.created_by.firebase_id or str(model_obj.created_by_id),
            description=model_obj.description,
            name=model_obj.name,
            nameKey=model_obj.name.lower().strip(),
            users=None,
            archivedBy=model_obj.modified_by.firebase_id or str(model_obj.modified_by_id) if model_obj.is_archived else None,
            archivedAt=int(model_obj.modified_at.timestamp() * 1000) if model_obj.is_archived else None,
        )

        fb_reference.set(
            value=firebase_utils.serialize(contributor_user_group_data),
        )

    @typing.override
    def handle_object_update_on_firebase(
        self,
        model_obj: ContributorUserGroup,
        fb_obj: firebase_ext_models.FbUserGroup,
        fb_reference: FbReference,
    ):
        fb_reference.update(
            value=firebase_utils.serialize(
                firebase_models.FbUserGroupUpdateInput(
                    description=model_obj.description,
                    name=model_obj.name,
                    nameKey=model_obj.name.lower().strip(),
                    archivedBy=model_obj.modified_by.firebase_id or str(model_obj.modified_by_id)
                    if model_obj.is_archived
                    else None,
                    archivedAt=int(model_obj.modified_at.timestamp() * 1000) if model_obj.is_archived else None,
                ),
            ),
        )

    @typing.override
    def get_firebase_path(self, firebase_id: str, model=ContributorUserGroup):
        return Config.FirebaseKeys.contributor_user_group(firebase_id)

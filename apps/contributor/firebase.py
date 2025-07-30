import logging

from celery import shared_task
from firebase_admin.db import Reference as FbReference
from pyfirebase_mapswipe import models as firebase_models
from pyfirebase_mapswipe import utils as firebase_utils

from apps.common.tasks import push_django_to_firebase
from apps.contributor.models import ContributorTeam
from main.config import Config

logger = logging.getLogger(__name__)


def handle_new_contributor_team_on_firebase(contributor_team: ContributorTeam, contributor_team_ref: FbReference):
    contributor_team_data = firebase_models.FbTeam(
        teamName=contributor_team.name,
        isArchived=contributor_team.is_archived,
        teamToken=str(contributor_team.token),
    )

    contributor_team_ref.set(
        value=firebase_utils.serialize(contributor_team_data),
    )


def handle_contributor_team_update_on_firebase(contributor_team: ContributorTeam, contributor_team_ref: FbReference):
    contributor_team_ref.update(
        value=firebase_utils.serialize(
            firebase_models.FbTeam(
                teamName=contributor_team.name,
                isArchived=contributor_team.is_archived,
                teamToken=str(contributor_team.token),
            ),
        ),
    )


@shared_task
def push_contributor_team_to_firebase(contributor_team_id: int):
    def get_firebase_path(canonical_id: str, team: ContributorTeam):
        return Config.FirebaseKeys.contributor_team(canonical_id)

    push_django_to_firebase(
        contributor_team_id,
        ContributorTeam,
        handle_new_contributor_team_on_firebase,
        handle_contributor_team_update_on_firebase,
        get_firebase_path,
    )

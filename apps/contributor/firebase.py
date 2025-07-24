import logging
import typing
from datetime import datetime

from celery import shared_task
from django.utils import timezone
from firebase_admin.db import Reference as FbReference
from pyfirebase_mapswipe import models as firebase_models
from pyfirebase_mapswipe import utils as firebase_utils

from apps.common.models import FirebasePushStatusEnum
from apps.contributor.models import ContributorTeam
from main.config import Config
from main.logging import log_extra

logger = logging.getLogger(__name__)


class InvalidContributorTeamPushException(Exception): ...


def handle_new_contributor_team_on_firebase(contributor_team: ContributorTeam, contributor_team_ref: FbReference):
    contributor_team_data = firebase_models.FbTeam(
        teamName=contributor_team.name,
        isArchived=contributor_team.is_archived,
        teamToken=datetime.now(),  # FIX: What is this used for?
    )

    contributor_team_ref.set(
        value={
            **firebase_utils.serialize(contributor_team_data),
        },
    )


def handle_contributor_team_update_on_firebase(contributor_team: ContributorTeam, contributor_team_ref: FbReference):
    contributor_team_ref.update(
        value=firebase_utils.serialize(
            firebase_models.FbTeam(
                teamName=contributor_team.name,
                isArchived=contributor_team.is_archived,
                teamToken=datetime.now(),  # FIX: What is this used for?
            ),
        ),
    )


@shared_task
def push_contributor_team_to_firebase(contributor_team_id: int):
    contributor_team = ContributorTeam.objects.filter(id=contributor_team_id).first()
    if not contributor_team:
        return
    contributor_team.update_firebase_push_status(FirebasePushStatusEnum.PROCESSING)

    try:
        contributor_team_ref = Config.FIREBASE_HELPER.ref(
            Config.FirebaseKeys.contributor_team(contributor_team.id),
        )
        fb_contributor_team: typing.Any = contributor_team_ref.get()

        if not contributor_team.firebase_last_pushed:
            if fb_contributor_team is not None:
                logger.error(
                    "push_to_firebase found a contributor_team already in firebase when creating a contributor_team",
                    extra=log_extra({"contributor_team": contributor_team.pk}),
                )
                raise InvalidContributorTeamPushException
            handle_new_contributor_team_on_firebase(contributor_team, contributor_team_ref)
        else:
            if fb_contributor_team is None:
                logger.error(
                    "push_to_firebase found did not find contributor_team in firebase when updating a contributor_team",
                    extra=log_extra({"contributor_team": contributor_team.pk}),
                )
                raise InvalidContributorTeamPushException
            handle_contributor_team_update_on_firebase(contributor_team, contributor_team_ref)
    except InvalidContributorTeamPushException:
        contributor_team.update_firebase_push_status(FirebasePushStatusEnum.FAILED)
    except Exception:
        logger.error(
            "push_to_firebase failed",
            extra=log_extra({"contributor_team": contributor_team.pk}),
            exc_info=True,
        )
        contributor_team.update_firebase_push_status(FirebasePushStatusEnum.FAILED)
    else:
        contributor_team.firebase_last_pushed = timezone.now()
        contributor_team.update_firebase_push_status(FirebasePushStatusEnum.SUCCESS, commit=False)
        contributor_team.save(
            update_fields=[
                "firebase_last_pushed",
                "firebase_push_status",
            ],
        )

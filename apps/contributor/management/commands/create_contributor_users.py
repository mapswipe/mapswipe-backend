import logging
import typing
import uuid

from django.core.management.base import BaseCommand
from django.utils import timezone
from pyfirebase_mapswipe import extended_models as firebase_extended_models
from pyfirebase_mapswipe import models as firebase_models
from pyfirebase_mapswipe import utils as firebase_utils

from apps.common.models import FirebasePushStatusEnum
from apps.contributor.factories import ContributorTeamFactory, ContributorUserFactory
from apps.contributor.models import ContributorTeam, ContributorUser
from apps.user.factories import UserFactory
from main.config import Config

logger = logging.getLogger(__name__)


def push_team_to_firebase(team: ContributorTeam):
    team.update_firebase_push_status(FirebasePushStatusEnum.PENDING)
    fb_reference = Config.FIREBASE_HELPER.ref(
        Config.FirebaseKeys.contributor_team(team.firebase_id),
    )
    contributor_team_data = firebase_models.FbTeam(
        teamName=team.name,
        isArchived=team.is_archived,
        teamToken=str(team.token),
    )
    fb_reference.set(
        value=firebase_utils.serialize(contributor_team_data),
    )
    team.update_firebase_push_status(FirebasePushStatusEnum.SUCCESS)


def push_team_member_to_firebase(member: ContributorUser):
    member.update_firebase_push_status(FirebasePushStatusEnum.PENDING)
    fb_reference = Config.FIREBASE_HELPER.ref(
        Config.FirebaseKeys.contributor_user(member.firebase_id),
    )
    team_member_data = firebase_extended_models.FbUser(
        userName=member.username,
        username=member.username,
        userNameKey=member.username.lower().strip(),
        usernameKey=member.username.lower().strip(),
        teamId=member.team.firebase_id if member.team else None,
        created=timezone.now(),
        lastAppUse=timezone.now(),
        taskContributionCount=0,
        groupContributionCount=0,
        projectContributionCount=0,
    )
    fb_reference.set(
        value=firebase_utils.serialize(team_member_data),
    )
    member.update_firebase_push_status(FirebasePushStatusEnum.SUCCESS)


class Command(BaseCommand):
    help = "Create dummy contributor users. Also sync these users to firebase"

    @typing.override
    def handle(self, *args, **options):  # type: ignore[reportMissingParameterType]
        if not Config.ENABLE_DANGER_MODE:
            logger.warning("Dummy data generation is disabled")
            return

        user = UserFactory.create(email=f"user-{uuid.uuid4()}@mapwsipe.com")
        user_resources = dict(
            created_by=user,
            modified_by=user,
            firebase_last_pushed=timezone.now(),
        )
        team_a, team_b = ContributorTeamFactory.create_batch(2, **user_resources)
        for team in [team_a, team_b]:
            push_team_to_firebase(team)

        team_a_members = ContributorUserFactory.create_batch(5, team=team_a, firebase_last_pushed=timezone.now())
        team_b_members = ContributorUserFactory.create_batch(5, team=team_b, firebase_last_pushed=timezone.now())
        no_team_members = ContributorUserFactory.create_batch(5, firebase_last_pushed=timezone.now())
        for team_members in [team_a_members, team_b_members, no_team_members]:
            for member in team_members:
                push_team_member_to_firebase(member)

        logger.info("Contributor users created successfully")

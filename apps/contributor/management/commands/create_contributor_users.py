import logging
import typing
import uuid

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from pyfirebase_mapswipe import extended_models as firebase_extended_models
from pyfirebase_mapswipe import models as firebase_models
from pyfirebase_mapswipe import utils as firebase_utils

from apps.contributor.factories import ContributorTeamFactory, ContributorUserFactory
from apps.contributor.models import ContributorTeam, ContributorUser
from apps.user.factories import UserFactory
from main.config import Config

logger = logging.getLogger(__name__)


def push_team_to_firebase(team: ContributorTeam):
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


def push_team_member_to_firebase(member: ContributorUser):
    fb_reference = Config.FIREBASE_HELPER.ref(
        Config.FirebaseKeys.contributor_user(member.firebase_id),
    )
    team_member_data = firebase_extended_models.FbUser(
        userName=member.username,
        username=member.username,
        userNameKey=member.username.lower(),
        usernameKey=member.username.lower(),
        teamId=member.team.firebase_id if member.team else firebase_models.UNDEFINED,
        created=timezone.now(),
    )
    fb_reference.set(
        value=firebase_utils.serialize(team_member_data),
    )


class Command(BaseCommand):
    help = "Create dummy contributor users. Also sync these users to firebase"

    @typing.override
    def handle(self, *args, **options):
        if not settings.ENABLE_DANGER_MODE:
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

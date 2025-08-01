import logging
import typing
import uuid

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.contributor.factories import ContributorTeamFactory, ContributorUserFactory
from apps.contributor.firebase import FirebaseContributorTeam
from apps.user.factories import UserFactory

logger = logging.getLogger(__name__)


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
        )
        team_a, team_b = ContributorTeamFactory.create_batch(2, **user_resources)
        for team in [team_a, team_b]:
            transaction.on_commit(lambda team_id=team.pk: FirebaseContributorTeam.task.delay(team_id))

        ContributorUserFactory.create_batch(5, team=team_a)
        ContributorUserFactory.create_batch(5, team=team_b)
        ContributorUserFactory.create_batch(20)

        logger.info("Contributor users created successfully")

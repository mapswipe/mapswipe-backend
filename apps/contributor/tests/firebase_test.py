import typing

from django.utils import timezone
from pyfirebase_mapswipe import extended_models as firebase_extended_models
from pyfirebase_mapswipe import utils as firebase_utils

from apps.contributor.factories import ContributorUserFactory
from apps.contributor.models import ContributorUser
from apps.contributor.tasks import pull_users_from_firebase
from main.config import Config
from main.tests import TestCase


class TestContributorFirebase(TestCase):
    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def _send_user_to_firebase(cls, member: ContributorUser, override_name: str | None = None):
        # NOTE: Usually user is created on the firebase but for testing purpose
        # we need to initialize some users in firebase from the backend
        fb_reference = Config.FIREBASE_HELPER.ref(Config.FirebaseKeys.contributor_user(member.firebase_id))
        username = override_name or member.username
        team_member_data = firebase_extended_models.FbUser(
            userName=username,
            username=username,
            userNameKey=username.lower().strip(),
            usernameKey=username.lower().strip(),
            teamId=member.team.firebase_id if member.team else None,
            created=timezone.now(),
        )
        fb_reference.set(
            value=firebase_utils.serialize(team_member_data),
        )

    @classmethod
    def _send_user_updates_to_firebase(cls, firebase_ids: list[str]):
        # NOTE: Usually user updates is created on the firebase but for testing purpose
        # we need to initialize some users in firebase from the backend
        fb_reference = Config.FIREBASE_HELPER.ref(Config.FirebaseKeys.contributor_user_updates())
        value = {key: True for key in firebase_ids}
        fb_reference.set(value=value)

    @classmethod
    def _read_user_updates_from_firebase(cls):
        # NOTE: Usually user updates is created on the firebase but for testing purpose
        # we need to initialize some users in firebase from the backend
        fb_reference = Config.FIREBASE_HELPER.ref(Config.FirebaseKeys.contributor_user_updates())
        return fb_reference.get()

    def test_users_pull_from_firebase(self):
        # Firebase Users:           Ram, Laxman, Shyam, Gita, Sita
        # Firebase User Updates:    Ram(u), Laxman(u), Gita(c), Sita(c), Hari(?), Ankit (?)
        # Database Users:           Ram, Laxman, Shyam, Ankit

        # Scenario: ram,laxman is in firebase and database (username is different)
        ram = ContributorUserFactory.create(username="ram")
        self._send_user_to_firebase(ram, override_name="Ram")
        laxman = ContributorUserFactory.create(username="laxman")
        self._send_user_to_firebase(laxman, override_name="Laxman")

        # Scenario: shyam is in firebase and database
        shyam = ContributorUserFactory.create(username="shyam")
        self._send_user_to_firebase(shyam)

        # Scenario: gita, sita is in firebase and needs to be synced to database
        gita = ContributorUserFactory.build(username="gita")
        self._send_user_to_firebase(gita)
        sita = ContributorUserFactory.build(username="sita")
        self._send_user_to_firebase(sita)

        # Scenario: hari is not in firebase and database
        hari = ContributorUserFactory.build(username="hari")

        # Scenario: ankit is not in firebase but is already in database.
        # Most probably inactive user that was deleted from firebase
        ankit = ContributorUserFactory.create(username="ankit")

        # Scenario: we have updates from the mapswipe firebase functions for the following users
        self._send_user_updates_to_firebase(
            [
                ram.firebase_id,
                laxman.firebase_id,
                gita.firebase_id,
                sita.firebase_id,
                hari.firebase_id,
                ankit.firebase_id,
            ],
        )

        assert ContributorUser.objects.all().count() == 4

        pull_users_from_firebase()

        # ram should be updated to Ram
        ram_updated = ContributorUser.objects.get(firebase_id=ram.firebase_id)
        assert ram_updated.username == "Ram"
        laxman_updated = ContributorUser.objects.get(firebase_id=laxman.firebase_id)
        assert laxman_updated.username == "Laxman"

        # gita, sita should be created
        ContributorUser.objects.get(firebase_id=gita.firebase_id)
        ContributorUser.objects.get(firebase_id=sita.firebase_id)

        # total users should increase by 1
        assert ContributorUser.objects.all().count() == 6

        # hari and ankit updates should not be removed from firebase
        assert self._read_user_updates_from_firebase() == {
            hari.firebase_id: True,
            ankit.firebase_id: True,
        }

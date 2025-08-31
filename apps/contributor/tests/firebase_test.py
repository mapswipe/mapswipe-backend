import datetime
import typing

import ulid
from django.utils import timezone
from pyfirebase_mapswipe import extended_models as firebase_extended_models
from pyfirebase_mapswipe import models as firebase_models
from pyfirebase_mapswipe import utils as firebase_utils

from apps.contributor.factories import ContributorUserFactory, ContributorUserGroupFactory
from apps.contributor.firebase.push import FirebaseContributorUserGroup
from apps.contributor.models import (
    ContributorUser,
    ContributorUserGroup,
    ContributorUserGroupMembership,
    ContributorUserGroupMembershipLog,
    ContributorUserGroupMembershipLogActionEnum,
)
from apps.contributor.tasks import pull_user_group_memberships_from_firebase, pull_users_from_firebase
from apps.user.factories import UserFactory
from main.config import Config
from main.tests import TestCase


class TestContributorFirebase(TestCase):
    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory.create()
        cls.user_resource_kwargs = dict(
            created_by=cls.user,
            modified_by=cls.user,
        )

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
    def _send_membership_request_to_firebase(
        cls,
        user: ContributorUser,
        user_group: ContributorUserGroup,
        action: ContributorUserGroupMembershipLogActionEnum,
        timestamp: int,
    ) -> str:
        unique_key = str(ulid.ULID())

        # NOTE: Usually membership join is created on the firebase
        membership_log_updates_ref = Config.FIREBASE_HELPER.ref(
            Config.FirebaseKeys.user_group_membership_log_update(unique_key),
        )
        membership_log_ref = Config.FIREBASE_HELPER.ref(Config.FirebaseKeys.user_group_membership_log(unique_key))

        log_data = firebase_models.FbUserGroupMembership(
            action=action.to_firebase(),
            timestamp=timestamp,
            userId=user.firebase_id,
            userGroupId=user_group.firebase_id,
        )

        membership_log_updates_ref.set(
            value=True,
        )
        membership_log_ref.set(
            value=firebase_utils.serialize(log_data),
        )

        return unique_key

    @classmethod
    def _send_user_updates_to_firebase(cls, firebase_ids: list[str]):
        # NOTE: Usually user updates is created on the firebase but for testing purpose
        # we need to initialize some users in firebase from the backend
        fb_reference = Config.FIREBASE_HELPER.ref(Config.FirebaseKeys.contributor_user_updates())
        value = {key: True for key in firebase_ids}
        fb_reference.set(value=value)

    @classmethod
    def _read_membership_request_from_firebase(cls):
        fb_reference = Config.FIREBASE_HELPER.ref(Config.FirebaseKeys.user_group_membership_log_updates())
        return fb_reference.get()

    @classmethod
    def _read_user_updates_from_firebase(cls):
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

    def test_user_group_memberships_from_firebase(self):
        # Firebase Users:                               Ram, Laxman, Sita
        # Firebase User Group:                          Ramayan
        # Firebase User Group Membership:               ...
        # Firebase User Group Membership Updates:       ...
        now = int(datetime.datetime.now().timestamp())

        # Create users in both firebase and database
        ram = ContributorUserFactory.create(username="ram")
        laxman = ContributorUserFactory.create(username="laxman")
        sita = ContributorUserFactory.create(username="sita")
        ravan = ContributorUserFactory.create(username="ravan")

        # NOTE: pandavs are not created in database yet
        yudhistir = ContributorUserFactory.build(username="yudhistir")
        bheem = ContributorUserFactory.build(username="bheem")

        self._send_user_to_firebase(ram)
        self._send_user_to_firebase(laxman)
        self._send_user_to_firebase(sita)
        self._send_user_to_firebase(ravan)

        self._send_user_to_firebase(yudhistir)
        self._send_user_to_firebase(bheem)

        # Create usergroups in both firebase and database
        ramayan = ContributorUserGroupFactory.create(
            **self.user_resource_kwargs,
            name="ramayan",
            description="one of the two important epics of Hinduism",
        )
        FirebaseContributorUserGroup(ramayan).trigger()

        # Pull 1: Ram joins
        self._send_membership_request_to_firebase(
            ram,
            ramayan,
            ContributorUserGroupMembershipLogActionEnum.JOIN,
            now,
        )
        # Pull 1: Sita joins
        self._send_membership_request_to_firebase(
            sita,
            ramayan,
            ContributorUserGroupMembershipLogActionEnum.JOIN,
            now,
        )
        pull_user_group_memberships_from_firebase()

        assert self._read_membership_request_from_firebase() is None
        assert ContributorUserGroupMembershipLog.objects.count() == 2
        assert ContributorUserGroupMembership.objects.count() == 2
        ram_membership = ContributorUserGroupMembership.objects.get(
            user_group_id=ramayan.id,
            user_id=ram.id,
        )
        assert ram_membership.is_active
        sita_membership = ContributorUserGroupMembership.objects.get(
            user_group_id=ramayan.id,
            user_id=sita.id,
        )
        assert sita_membership.is_active

        # Pull 2: Laxman joins
        self._send_membership_request_to_firebase(
            laxman,
            ramayan,
            ContributorUserGroupMembershipLogActionEnum.JOIN,
            now + 1,
        )
        pull_user_group_memberships_from_firebase()

        assert self._read_membership_request_from_firebase() is None
        assert ContributorUserGroupMembershipLog.objects.count() == 3
        assert ContributorUserGroupMembership.objects.count() == 3
        laxman_membership = ContributorUserGroupMembership.objects.get(
            user_group=ramayan.id,
            user=laxman.id,
        )
        assert laxman_membership.is_active

        # Pull 3: Ram leaves but joins again
        self._send_membership_request_to_firebase(
            ram,
            ramayan,
            ContributorUserGroupMembershipLogActionEnum.LEAVE,
            now + 2,
        )
        self._send_membership_request_to_firebase(
            ram,
            ramayan,
            ContributorUserGroupMembershipLogActionEnum.JOIN,
            now + 3,
        )
        # Pull 3: Laxman leaves, joins and leaves again
        self._send_membership_request_to_firebase(
            laxman,
            ramayan,
            ContributorUserGroupMembershipLogActionEnum.LEAVE,
            now + 2,
        )
        self._send_membership_request_to_firebase(
            laxman,
            ramayan,
            ContributorUserGroupMembershipLogActionEnum.JOIN,
            now + 3,
        )
        self._send_membership_request_to_firebase(
            laxman,
            ramayan,
            ContributorUserGroupMembershipLogActionEnum.LEAVE,
            now + 4,
        )
        # Pull 3: Sita joins and leaves (but this action occurred on Pull 0)
        # NOTE: This should not deactivate Sita
        self._send_membership_request_to_firebase(
            sita,
            ramayan,
            ContributorUserGroupMembershipLogActionEnum.JOIN,
            now - 2,
        )
        self._send_membership_request_to_firebase(
            sita,
            ramayan,
            ContributorUserGroupMembershipLogActionEnum.LEAVE,
            now - 1,
        )
        pull_user_group_memberships_from_firebase()

        assert self._read_membership_request_from_firebase() is None
        assert ContributorUserGroupMembershipLog.objects.count() == 10
        assert ContributorUserGroupMembership.objects.count() == 3
        ram_membership = ContributorUserGroupMembership.objects.get(
            user_group=ramayan.id,
            user=ram.id,
        )
        assert ram_membership.is_active
        laxman_membership = ContributorUserGroupMembership.objects.get(
            user_group=ramayan.id,
            user=laxman.id,
        )
        assert not laxman_membership.is_active
        # There should be no change in sita
        sita_membership = ContributorUserGroupMembership.objects.get(
            user_group=ramayan.id,
            user=sita.id,
        )
        assert sita_membership.is_active

        # Pull 4: yudhistir joins (but user is not in database)
        yudhistir_membership_key = self._send_membership_request_to_firebase(
            yudhistir,
            ramayan,
            ContributorUserGroupMembershipLogActionEnum.JOIN,
            now + 5,
        )
        bheem_membership_key = self._send_membership_request_to_firebase(
            bheem,
            ramayan,
            ContributorUserGroupMembershipLogActionEnum.JOIN,
            now + 5,
        )
        self._send_membership_request_to_firebase(
            ravan,
            ramayan,
            ContributorUserGroupMembershipLogActionEnum.JOIN,
            now + 5,
        )
        pull_user_group_memberships_from_firebase()

        assert self._read_membership_request_from_firebase() == {
            yudhistir_membership_key: True,
            bheem_membership_key: True,
        }
        assert ContributorUserGroupMembershipLog.objects.count() == 11
        assert ContributorUserGroupMembership.objects.count() == 4

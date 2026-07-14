from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError

from apps.contributor.factories import ContributorUserFactory
from apps.contributor.models import ContributorUser
from main.config import Config
from main.tests import TestCase

FH = Config.FIREBASE_HELPER
K = Config.FirebaseKeys


def osm_key(firebase_id: str) -> str:
    return f"/v2/OSMAccessToken/{firebase_id}"


class TestAnonymizeUserFromFirebase(TestCase):
    """Anonymization must scrub only the target user's PII (name fields, OSM token, auth account)
    while leaving every pseudonymous node keyed by their uid (results, groupsUsers, memberships)
    and all other users/data untouched.
    """

    TARGET_UID = "target-user-uid"
    OTHER_UID = "other-user-uid"
    PROJECT_FID = "project-fid"
    GROUP_ID = "group-fid"
    USER_GROUP_ID = "user-group-fid"
    MEMBERSHIP_LOG_ID = "membership-log-fid"

    def _seed(self, path: str, value: object) -> None:
        FH.ref(path).set(value=value)

    def _get(self, path: str) -> object:
        return FH.ref(path).get()

    def _target_user_node(self) -> dict[str, object]:
        return {
            # PII (the four legacy name fields) -- must be scrubbed.
            "userName": "Alice Real",
            "username": "Alice Real",
            "userNameKey": "alice real",
            "usernameKey": "alice real",
            # Pseudonymous -- must be preserved.
            "created": "2025-01-01T00:00:00.000Z",
            "lastAppUse": "2025-06-01T00:00:00.000Z",
            "taskContributionCount": 227,
            "groupContributionCount": 5,
            "projectContributionCount": 2,
            "accessibility": {"darkMode": True},
            "userGroups": {self.USER_GROUP_ID: True},
            "contributions": {self.PROJECT_FID: {self.GROUP_ID: True, "taskContributionCount": 5}},
        }

    def _seed_world(self, target: ContributorUser) -> dict[str, object]:
        """Seed the target profile + every pseudonymous node keyed by their uid + unrelated data.

        Returns ``survivors`` = {path: value} that must remain byte-for-byte after anonymization.
        """
        uid = target.firebase_id

        # Target user's profile node and OSM access token.
        self._seed(K.contributor_user(uid), self._target_user_node())
        self._seed(osm_key(uid), {"token": "osm-secret", "createdAt": 1700000000})

        # Pseudonymous nodes referencing the target uid (no name embedded) -- must survive.
        self._seed(
            f"/v2/results/{self.PROJECT_FID}/{self.GROUP_ID}/{uid}",
            {"startTime": "t0", "endTime": "t1", "results": {"task-1": 1}},
        )
        self._seed(f"/v2/groupsUsers/{self.PROJECT_FID}/{self.GROUP_ID}/{uid}", True)
        self._seed(f"/v2/userGroups/{self.USER_GROUP_ID}/users/{uid}", True)
        self._seed(
            K.user_group_membership_log(self.MEMBERSHIP_LOG_ID),
            {"action": 1, "userId": uid, "userGroupId": self.USER_GROUP_ID},
        )

        # Another user -- must be untouched entirely (name AND OSM token).
        self._seed(
            K.contributor_user(self.OTHER_UID),
            {"username": "Bob", "usernameKey": "bob", "taskContributionCount": 3},
        )
        self._seed(osm_key(self.OTHER_UID), {"token": "bob-token"})

        # Unrelated global data.
        self._seed(K.announcement(), {"text": "hi"})

        survivor_paths = [
            f"/v2/results/{self.PROJECT_FID}/{self.GROUP_ID}/{uid}",
            f"/v2/groupsUsers/{self.PROJECT_FID}/{self.GROUP_ID}/{uid}",
            f"/v2/userGroups/{self.USER_GROUP_ID}/users/{uid}",
            K.user_group_membership_log(self.MEMBERSHIP_LOG_ID),
            K.contributor_user(self.OTHER_UID),
            osm_key(self.OTHER_UID),
            K.announcement(),
        ]
        return {path: self._get(path) for path in survivor_paths}

    def _assert_survivors_unchanged(self, survivors: dict[str, object]) -> None:
        for path, value in survivors.items():
            assert self._get(path) == value, f"unrelated/pseudonymous data at {path} must be unchanged"

    def test_anonymizes_only_target_pii(self):
        target = ContributorUserFactory.create(username="Alice Real", firebase_id=self.TARGET_UID)
        survivors = self._seed_world(target)

        with mock.patch.object(FH.auth, "delete_user") as mock_auth_delete:
            call_command("anonymize_user_from_firebase", "--user-id", str(target.pk), "--yes")

        # Firebase auth account is deleted.
        mock_auth_delete.assert_called_once_with(self.TARGET_UID)

        node = self._get(K.contributor_user(self.TARGET_UID))
        assert isinstance(node, dict)
        # Name fields scrubbed.
        assert node["userName"] == "Deleted User"
        assert node["username"] == "Deleted User"
        assert node["userNameKey"] == "deleted user"
        assert node["usernameKey"] == "deleted user"
        # Pseudonymous fields preserved.
        assert node["taskContributionCount"] == 227
        assert node["contributions"] == {self.PROJECT_FID: {self.GROUP_ID: True, "taskContributionCount": 5}}
        assert node["userGroups"] == {self.USER_GROUP_ID: True}
        assert node["accessibility"] == {"darkMode": True}
        assert node["created"] == "2025-01-01T00:00:00.000Z"

        # OSM token deleted for the target only.
        assert self._get(osm_key(self.TARGET_UID)) is None

        # Postgres username anonymized.
        target.refresh_from_db()
        assert target.username == "Deleted User"

        self._assert_survivors_unchanged(survivors)

    def test_dry_run_changes_nothing(self):
        target = ContributorUserFactory.create(username="Alice Real", firebase_id=self.TARGET_UID)
        survivors = self._seed_world(target)
        original_node = self._get(K.contributor_user(self.TARGET_UID))

        with mock.patch.object(FH.auth, "delete_user") as mock_auth_delete:
            call_command("anonymize_user_from_firebase", "--user-id", str(target.pk), "--dry-run")

        mock_auth_delete.assert_not_called()
        assert self._get(K.contributor_user(self.TARGET_UID)) == original_node
        assert self._get(osm_key(self.TARGET_UID)) is not None
        target.refresh_from_db()
        assert target.username == "Alice Real"
        self._assert_survivors_unchanged(survivors)

    def test_select_by_firebase_id(self):
        target = ContributorUserFactory.create(username="Alice Real", firebase_id=self.TARGET_UID)
        self._seed_world(target)

        with mock.patch.object(FH.auth, "delete_user") as mock_auth_delete:
            call_command("anonymize_user_from_firebase", "--firebase-id", self.TARGET_UID, "--yes")

        mock_auth_delete.assert_called_once_with(self.TARGET_UID)
        node = self._get(K.contributor_user(self.TARGET_UID))
        assert isinstance(node, dict)
        assert node["username"] == "Deleted User"

    def test_requires_selection(self):
        with self.assertRaises(CommandError):
            call_command("anonymize_user_from_firebase", "--yes")

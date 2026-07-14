import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.project.models import Project, ProjectStatusEnum
from apps.user.factories import UserFactory
from main.config import Config
from main.tests import TestCase

FH = Config.FIREBASE_HELPER
K = Config.FirebaseKeys

# Routes with no dedicated FirebaseKeys helper.
UPDATES_USER_GROUPS_KEY = "/v2/updates/userGroups"


def osm_access_token_key(uid: str) -> str:
    return f"/v2/OSMAccessToken/{uid}"


class TestDeleteProjectFromFirebase(TestCase):
    """Every test starts from a base that seeds all 13 top-level ``/v2`` routes.

    The base includes routes created only by the Firebase Cloud Functions (groupsUsers,
    per-user contributions/counters, OSMAccessToken, the updates/* queues) so we can prove
    the deletion command removes only the target project's nodes and nothing else.

    ``/backendWait`` is the one route outside ``/v2``. The harness only resets ``/v2`` between
    tests, so we seed it and register an explicit cleanup to avoid leaking it across tests.
    """

    CONTRIB_UID = "contributing-user-fid"
    OTHER_UID = "another-user-fid"
    USER_GROUP_ID = "user-group-fid"
    MEMBERSHIP_LOG_ID = "membership-log-fid"
    TEAM_ID = "team-fid"
    ORG_ID = "organisation-fid"

    def _seed(self, path: str, value: object) -> None:
        FH.ref(path).set(value=value)

    def _get(self, path: str) -> object:
        return FH.ref(path).get()

    def _make_project(self, status: ProjectStatusEnum = ProjectStatusEnum.FINISHED) -> Project:
        user = UserFactory.create()
        organization = OrganizationFactory.create(created_by=user, modified_by=user)
        return ProjectFactory.create(
            status=status,
            firebase_last_pushed=timezone.now(),
            created_by=user,
            modified_by=user,
            requesting_organization=organization,
        )

    def _project_nodes(self, firebase_id: str) -> dict[str, str]:
        """The five per-project nodes (four backend-owned + cloud-function groupsUsers)."""
        return {
            "project": K.project(firebase_id),
            "groups": K.project_groups(firebase_id),
            "tasks": K.project_tasks(firebase_id),
            "results": K.results_project_groups(firebase_id),
            "groupsUsers": K.project_group_users(firebase_id),
        }

    def _seed_world(self, target: Project, other: Project) -> tuple[dict[str, str], dict[str, object]]:
        """Seed every known ``/v2`` route.

        Returns ``(target_nodes, survivors)`` where ``target_nodes`` is ``{label: path}`` for
        the project being deleted, and ``survivors`` is ``{path: value}`` for everything that
        must remain byte-for-byte after deletion (values captured as Firebase normalized them).
        """
        target_nodes = self._project_nodes(target.firebase_id)
        other_nodes = self._project_nodes(other.firebase_id)

        # --- project subtrees: /v2/{projects,groups,tasks,results,groupsUsers}/{id} ---
        for label, path in target_nodes.items():
            self._seed(path, {"seeded": f"target-{label}"})
        for label, path in other_nodes.items():
            self._seed(path, {"seeded": f"other-{label}"})

        # --- /v2/users/{uid} : full node incl. cloud-function-written children ---
        self._seed(
            K.contributor_user(self.CONTRIB_UID),
            {
                "username": "mapper",
                "usernameKey": "mapper",
                "created": "2025-01-01T00:00:00.000Z",
                "lastAppUse": "2025-06-01T00:00:00.000Z",
                "taskContributionCount": 227,
                "groupContributionCount": 5,
                "projectContributionCount": 2,
                "accessibility": {"darkMode": True},
                "userGroups": {self.USER_GROUP_ID: True},
                "contributions": {
                    # contributions to the DELETED project must remain (user history).
                    target.firebase_id: {"g1": True, "taskContributionCount": 5},
                    other.firebase_id: {"g2": True, "taskContributionCount": 9},
                },
            },
        )
        self._seed(K.contributor_user(self.OTHER_UID), {"username": "bystander", "taskContributionCount": 0})

        # --- /v2/OSMAccessToken/{uid} (cloud function / OSM auth) ---
        self._seed(osm_access_token_key(self.CONTRIB_UID), {"token": "osm-token", "createdAt": 1700000000})

        # --- /v2/userGroups/{gid} (with nested users child) ---
        self._seed(
            K.contributor_user_group(self.USER_GROUP_ID),
            {"name": "Team Alpha", "users": {self.CONTRIB_UID: True}},
        )

        # --- /v2/userGroupMembershipLogs/{logId} ---
        self._seed(
            K.user_group_membership_log(self.MEMBERSHIP_LOG_ID),
            {"action": 1, "timestamp": 1700000000, "userId": self.CONTRIB_UID, "userGroupId": self.USER_GROUP_ID},
        )

        # --- /v2/updates/* queues (all three, incl. the never-consumed userGroups queue) ---
        self._seed(K.contributor_user_updates(), {self.CONTRIB_UID: True})
        self._seed(K.user_group_membership_log_updates(), {self.MEMBERSHIP_LOG_ID: True})
        self._seed(UPDATES_USER_GROUPS_KEY, {self.USER_GROUP_ID: True})

        # --- /v2/teams/{teamId} ---
        self._seed(K.contributor_team(self.TEAM_ID), {"teamName": "A Team", "teamToken": "team-token"})

        # --- /v2/organisations/{orgId} ---
        self._seed(K.organization(self.ORG_ID), {"name": "An Org", "description": "desc"})

        # --- /v2/announcement ---
        self._seed(K.announcement(), {"text": "hello", "url": "https://example.com"})

        # --- /backendWait (outside /v2; harness does not reset it, so clean up explicitly) ---
        self._seed(K.backend_wait(), {"ok": True, "timestamp": "2025-01-01T00:00:00+00:00"})
        self.addCleanup(lambda: FH.ref(K.backend_wait()).delete())

        # Everything that is NOT a target project node must survive unchanged.
        survivor_paths = [
            *other_nodes.values(),
            K.contributor_user(self.CONTRIB_UID),
            K.contributor_user(self.OTHER_UID),
            osm_access_token_key(self.CONTRIB_UID),
            K.contributor_user_group(self.USER_GROUP_ID),
            K.user_group_membership_log(self.MEMBERSHIP_LOG_ID),
            K.contributor_user_updates(),
            K.user_group_membership_log_updates(),
            UPDATES_USER_GROUPS_KEY,
            K.contributor_team(self.TEAM_ID),
            K.organization(self.ORG_ID),
            K.announcement(),
            K.backend_wait(),
        ]
        # Capture values as Firebase stored them, so assertions are normalization-proof.
        survivors = {path: self._get(path) for path in survivor_paths}
        return target_nodes, survivors

    def _assert_survivors_unchanged(self, survivors: dict[str, object]) -> None:
        for path, value in survivors.items():
            assert self._get(path) == value, f"unrelated data at {path} must be unchanged"

    def test_deletes_only_target_project_nodes(self):
        target = self._make_project()
        other = self._make_project()
        target_nodes, survivors = self._seed_world(target, other)

        call_command("delete_project_from_firebase", "--project-id", str(target.pk), "--yes")

        for label, path in target_nodes.items():
            assert self._get(path) is None, f"target project '{label}' node should be deleted"
        self._assert_survivors_unchanged(survivors)

    def test_dry_run_deletes_nothing(self):
        target = self._make_project()
        other = self._make_project()
        target_nodes, survivors = self._seed_world(target, other)

        call_command("delete_project_from_firebase", "--project-id", str(target.pk), "--dry-run")

        # Even the target survives a dry run.
        for label, path in target_nodes.items():
            assert self._get(path) is not None, f"dry-run must not delete '{label}'"
        self._assert_survivors_unchanged(survivors)

    def test_withdrawn_project_selected_by_status(self):
        target = self._make_project(status=ProjectStatusEnum.WITHDRAWN)
        other = self._make_project()  # finished, not selected by --status withdrawn
        target_nodes, survivors = self._seed_world(target, other)

        call_command("delete_project_from_firebase", "--status", "withdrawn", "--yes")

        for label, path in target_nodes.items():
            assert self._get(path) is None, f"withdrawn project '{label}' node should be deleted"
        self._assert_survivors_unchanged(survivors)

    def test_refuses_ineligible_status(self):
        published = self._make_project(status=ProjectStatusEnum.PUBLISHED)
        other = self._make_project()
        published_nodes, survivors = self._seed_world(published, other)

        with pytest.raises(CommandError):
            call_command("delete_project_from_firebase", "--project-id", str(published.pk), "--yes")

        # Nothing should have been deleted for a non finished/withdrawn project.
        for label, path in published_nodes.items():
            assert self._get(path) is not None, f"published project '{label}' must not be deleted"
        self._assert_survivors_unchanged(survivors)

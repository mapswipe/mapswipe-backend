"""Regression tests for the PUBLISHED -> FINISHED firebase push race condition.

Bug: when a stats push (only_stats=True) and a status-change push raced for
the same project, the finish push was rejected by the PENDING guard, leaving
the project visible in Firebase even though DB showed FINISHED.

Fix: replaced the firebase_push_status PENDING gate with version numbers.
  firebase_push_requested_version — bumped by every trigger
  firebase_pushed_version         — recorded on push success (snapshot from start)

The push task checks pushed >= requested and skips if already up-to-date.
A trailing-edge re-enqueue heals the lock-drop path.
"""

import typing
from unittest.mock import patch

from django.utils import timezone

from apps.common.models import FirebasePushStatusEnum
from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.project.models import Project
from apps.project.tasks import push_project_to_firebase
from apps.user.factories import UserFactory
from main.cache import CeleryLock
from main.cache import cache as celery_lock_cache
from main.tests import TestCase
from project_types.store import get_project_type_handler
from project_types.tile_map_service.find.project import FindProjectProperty
from utils.geo.raster_tile_server.config import RasterTileServerNameEnum
from utils.geo.raster_tile_server.models import RasterTileServerCommonConfig, RasterTileServerConfig


def _find_project_specifics() -> dict[str, typing.Any]:
    return FindProjectProperty(
        zoom_level=14,
        tile_server_property=RasterTileServerConfig(
            name=RasterTileServerNameEnum.BING,
            bing=RasterTileServerCommonConfig(credits="test"),
        ),
        aoi_geometry="1",
    ).model_dump()


class TestFirebasePushRaceConditionFixed(TestCase):
    """Verifies the version-based fix prevents false FAILED and silent lock-drops."""

    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory.create()
        cls.user_kwargs = dict(created_by=cls.user, modified_by=cls.user)
        cls.organization = OrganizationFactory.create(**cls.user_kwargs)

    def _published_project(self, **kwargs: typing.Any) -> Project:
        return ProjectFactory.create(
            **self.user_kwargs,
            requesting_organization=self.organization,
            status=Project.Status.PUBLISHED,
            firebase_push_status=FirebasePushStatusEnum.SUCCESS,
            firebase_last_pushed=timezone.now(),
            project_type_specifics=_find_project_specifics(),
            **kwargs,
        )

    def test_already_up_to_date_is_noop_not_failed(self):
        """Old: firebase_push_status=SUCCESS -> guard fails -> FAILED.

        New: pushed_version >= requested_version → early return, no FAILED.
        """
        project = self._published_project(
            firebase_push_requested_version=1,
            firebase_pushed_version=1,  # already satisfied
        )
        Project.objects.filter(pk=project.pk).update(status=Project.Status.FINISHED)

        project_from_db = Project.objects.get(pk=project.pk)
        handler = get_project_type_handler(project_from_db.project_type_enum)(project_from_db)
        handler.push_project_on_firebase()

        project.refresh_from_db()
        # Should remain SUCCESS (no exception, no FAILED)
        assert project.firebase_push_status_enum == FirebasePushStatusEnum.SUCCESS
        assert project.status_enum == Project.Status.FINISHED

    def test_task_path_already_up_to_date_is_noop(self):
        """Same via the full task entry point."""
        project = self._published_project(
            firebase_push_requested_version=2,
            firebase_pushed_version=2,
        )
        Project.objects.filter(pk=project.pk).update(status=Project.Status.FINISHED)

        push_project_to_firebase(project.pk)

        project.refresh_from_db()
        assert project.firebase_push_status_enum == FirebasePushStatusEnum.SUCCESS
        assert project.status_enum == Project.Status.FINISHED

    def test_lock_drop_still_returns_none(self):
        """Lock-drop path unchanged: task returns None when lock is held."""
        project = self._published_project(
            firebase_push_requested_version=1,
            firebase_pushed_version=0,
        )
        Project.objects.filter(pk=project.pk).update(status=Project.Status.FINISHED)

        lock_key = CeleryLock.Key.PUSH_PROJECT_TO_FIREBASE.format(project.pk)
        celery_lock_cache.add(lock_key, 1, 60)

        try:
            result = push_project_to_firebase(project.pk)
            assert result is None
        finally:
            celery_lock_cache.delete(lock_key)

    def test_request_firebase_push_increments_version(self):
        """request_firebase_push() atomically bumps requested_version."""
        project = self._published_project(
            firebase_push_requested_version=0,
            firebase_pushed_version=0,
        )
        project.request_firebase_push()
        project.refresh_from_db()
        assert project.firebase_push_requested_version == 1
        assert project.firebase_pushed_version == 0

    def test_trailing_edge_reenqueue_satisfies_concurrent_version_bump(self):
        """T1 snapshots v1; concurrent bump sets requested=2 mid-push;
        T1 success -> trailing-edge re-enqueues T3; T3 satisfies v2.

        This also covers the lock-drop path: T2 was dropped by the lock while
        T1 held it, but T1's trailing-edge re-enqueue heals the gap.
        """
        project = self._published_project(
            firebase_push_requested_version=1,
            firebase_pushed_version=0,
        )

        # T1 loads the project — snapshot will be v1
        project_from_db = Project.objects.get(pk=project.pk)

        # Concurrent request (T2) bumps to v2 while T1 is "in flight"
        Project.objects.filter(pk=project.pk).update(firebase_push_requested_version=2)

        handler = get_project_type_handler(project_from_db.project_type_enum)(project_from_db)

        with (
            patch("project_types.base.project.BaseProject._push_project_on_firebase"),
            self.captureOnCommitCallbacks(execute=True),
        ):
            handler.push_project_on_firebase()

        project.refresh_from_db()
        # T1 satisfied v1, trailing-edge re-enqueued T3, T3 satisfied v2
        assert project.firebase_pushed_version == 2
        assert project.firebase_push_status_enum == FirebasePushStatusEnum.SUCCESS

    def test_no_trailing_edge_reenqueue_when_no_concurrent_bump(self):
        """No new request during push → no re-enqueue, pushed_version=requested_version."""
        project = self._published_project(
            firebase_push_requested_version=1,
            firebase_pushed_version=0,
        )
        project_from_db = Project.objects.get(pk=project.pk)
        handler = get_project_type_handler(project_from_db.project_type_enum)(project_from_db)

        with (
            patch("project_types.base.project.BaseProject._push_project_on_firebase"),
            self.captureOnCommitCallbacks(execute=False) as callbacks,
        ):
            handler.push_project_on_firebase()

        assert callbacks == []
        project.refresh_from_db()
        assert project.firebase_pushed_version == 1
        assert project.firebase_push_status_enum == FirebasePushStatusEnum.SUCCESS

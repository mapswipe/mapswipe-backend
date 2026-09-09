import typing
from unittest.mock import patch

import pytest
from celery.exceptions import MaxRetriesExceededError

from apps.common.models import FirebasePushStatusEnum
from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.project.models import Project, ProjectTypeEnum
from apps.project.tasks import push_project_to_firebase
from apps.tutorial.factories import TutorialFactory
from apps.tutorial.models import Tutorial
from apps.user.factories import UserFactory
from main.cache import CeleryLock, cache
from main.config import Config
from main.tests import TestCase


class TestFirebasePushRace(TestCase):
    """Regression tests for the PUBLISHED -> FINISHED firebase sync race.

    A stats push and the finish push both expect
    firebase_push_status == PENDING. Whichever runs second used to see SUCCESS
    (set by the first) and get rejected by a guard, leaving the project FINISHED
    in the DB but still visible/active in Firebase.
    """

    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory.create()
        cls.user_resource_kwargs = dict(created_by=cls.user, modified_by=cls.user)
        cls.organization = OrganizationFactory.create(**cls.user_resource_kwargs)

    def _build_published_project(self) -> Project:
        # NOTE: Built directly in PUBLISHED status via the ORM rather than by driving
        # the real DRAFT -> ... -> PUBLISHED pipeline through mutations: this suite is
        # only exercising the firebase push race, not project processing/publishing
        # itself (already covered by apps/project/tests/e2e_create_*_test.py).
        proj = ProjectFactory.create(
            **self.user_resource_kwargs,
            project_type=ProjectTypeEnum.VALIDATE_IMAGE,
            topic="Firebase Race Project",
            region="Test Region",
            project_number=1,
            requesting_organization=self.organization,
            status=Project.Status.PUBLISHED,
            project_type_specifics={"source_type": "DIRECT_IMAGES"},
        )
        tutorial = TutorialFactory.create(
            **self.user_resource_kwargs,
            project=proj,
            status=Tutorial.Status.PUBLISHED,
        )
        proj.tutorial = tutorial
        proj.save(update_fields=["tutorial"])

        # NOTE: Every real push trigger marks PENDING before queueing (this is the flag
        # this suite's race is about, not a precondition this fix relies on) -- set it
        # here too so this initial, uncontested push isn't itself mistaken for a race.
        proj.update_firebase_push_status(FirebasePushStatusEnum.PENDING)
        push_project_to_firebase(project_id=proj.pk)

        proj.refresh_from_db()
        assert proj.status == Project.Status.PUBLISHED
        assert proj.firebase_push_status_enum == FirebasePushStatusEnum.SUCCESS
        assert proj.firebase_last_pushed is not None

        return proj

    def test_second_push_after_finish_is_not_rejected(self):
        proj = self._build_published_project()

        project_ref = self.firebase_helper.ref(Config.FirebaseKeys.project(proj.firebase_id))
        fb_project: typing.Any = project_ref.get()
        assert fb_project is not None
        assert fb_project["status"] == "active"

        # Commit the status transition directly, mirroring exactly what
        # ProjectStatusUpdateSerializer.update commits before queueing its push:
        # status flips to FINISHED and firebase_push_status is (re)marked PENDING.
        Project.objects.filter(pk=proj.pk).update(
            status=Project.Status.FINISHED,
            firebase_push_status=FirebasePushStatusEnum.PENDING,
        )

        # PushA: a second, independently-queued push (e.g. a stats push) runs
        # first and completes, flipping firebase_push_status PENDING -> SUCCESS.
        push_project_to_firebase(project_id=proj.pk)
        proj.refresh_from_db()
        assert proj.firebase_push_status_enum == FirebasePushStatusEnum.SUCCESS

        # PushB: the finish push itself now runs. Before this fix, it would see
        # firebase_push_status == SUCCESS (not PENDING) and raise
        # ValidationException, landing on FAILED with `status` never written to
        # Firebase -- exactly the project-3012 bug. It must now succeed.
        push_project_to_firebase(project_id=proj.pk)

        proj.refresh_from_db()
        assert proj.status == Project.Status.FINISHED
        assert proj.firebase_push_status_enum == FirebasePushStatusEnum.SUCCESS

        fb_project = project_ref.get()
        assert fb_project["status"] == "finished"

    def test_lock_contention_retries_instead_of_dropping(self):
        proj = self._build_published_project()

        lock_key = CeleryLock.Key.PUSH_PROJECT_TO_FIREBASE.format(proj.pk)
        assert cache.add(lock_key, 1, 30)  # simulate another push currently holding the lock

        try:
            with patch("apps.project.tasks.current_task") as mock_current_task:
                mock_current_task.request.retries = 0
                mock_current_task.retry.side_effect = Exception("retry-requested")

                with self.assertRaisesMessage(Exception, "retry-requested"):
                    push_project_to_firebase(project_id=proj.pk)

                mock_current_task.retry.assert_called_once_with(countdown=1, max_retries=5)
        finally:
            cache.delete(lock_key)

        # Firebase push status must be untouched: the push body never ran.
        proj.refresh_from_db()
        assert proj.firebase_push_status_enum == FirebasePushStatusEnum.SUCCESS

    def test_lock_contention_gives_up_after_max_retries(self):
        proj = self._build_published_project()

        lock_key = CeleryLock.Key.PUSH_PROJECT_TO_FIREBASE.format(proj.pk)
        assert cache.add(lock_key, 1, 30)  # simulate another push currently holding the lock

        try:
            # `retries=5` simulates "this is the 6th attempt" without actually looping
            # through 5 real retries. Celery's own Task.retry() then sees
            # request.retries (5) >= max_retries (5) and raises MaxRetriesExceededError
            # instead of scheduling another attempt -- this is real Celery retry-cap
            # behavior, not something we implement ourselves.
            with pytest.raises(MaxRetriesExceededError):
                push_project_to_firebase.apply(kwargs={"project_id": proj.pk}, retries=5)
        finally:
            cache.delete(lock_key)

        # Firebase push status must be untouched: the push body never ran.
        proj.refresh_from_db()
        assert proj.firebase_push_status_enum == FirebasePushStatusEnum.SUCCESS

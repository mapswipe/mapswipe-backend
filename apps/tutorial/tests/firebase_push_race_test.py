import typing
from unittest.mock import patch

import pytest
from celery.exceptions import MaxRetriesExceededError

from apps.common.models import FirebasePushStatusEnum
from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.project.models import ProjectTypeEnum
from apps.tutorial.factories import TutorialFactory
from apps.tutorial.models import Tutorial
from apps.tutorial.tasks import push_tutorial_to_firebase
from apps.user.factories import UserFactory
from main.cache import CeleryLock, cache
from main.config import Config
from main.tests import TestCase


class TestTutorialFirebasePushRace(TestCase):
    """Regression tests for the same firebase push race as project (see
    apps/project/tests/firebase_push_race_test.py) applied to tutorials.

    Tutorial has an identical structural shape: a content-edit push
    (apps/tutorial/serializers.py:471) and a status-change push (:602) both
    independently queue push_tutorial_to_firebase for the same tutorial, sharing a
    single firebase_push_status PENDING guard.
    """

    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory.create()
        cls.user_resource_kwargs = dict(created_by=cls.user, modified_by=cls.user)
        cls.organization = OrganizationFactory.create(**cls.user_resource_kwargs)

    def _build_published_tutorial(self) -> Tutorial:
        project = ProjectFactory.create(
            **self.user_resource_kwargs,
            project_type=ProjectTypeEnum.VALIDATE_IMAGE,
            topic="Tutorial Race Project",
            region="Test Region",
            project_number=1,
            requesting_organization=self.organization,
            project_type_specifics={"source_type": "DIRECT_IMAGES"},
        )
        tutorial = TutorialFactory.create(
            **self.user_resource_kwargs,
            project=project,
            name="Tutorial Race Demo",
            status=Tutorial.Status.PUBLISHED,
        )
        tutorial.update_firebase_push_status(FirebasePushStatusEnum.PENDING)
        push_tutorial_to_firebase(tutorial_id=tutorial.pk)

        tutorial.refresh_from_db()
        assert tutorial.status_enum == Tutorial.Status.PUBLISHED
        assert tutorial.firebase_push_status_enum == FirebasePushStatusEnum.SUCCESS
        assert tutorial.firebase_last_pushed is not None

        return tutorial

    def test_second_push_after_archive_is_not_rejected(self):
        tutorial = self._build_published_tutorial()

        tutorial_ref = self.firebase_helper.ref(Config.FirebaseKeys.tutorial(tutorial.firebase_id))
        fb_tutorial: typing.Any = tutorial_ref.get()
        assert fb_tutorial is not None

        # Commit the status transition directly, mirroring what
        # TutorialStatusUpdateSerializer.update commits before queueing its push.
        Tutorial.objects.filter(pk=tutorial.pk).update(
            status=Tutorial.Status.ARCHIVED,
            firebase_push_status=FirebasePushStatusEnum.PENDING,
        )

        # PushA: a content-edit push runs first and completes, flipping
        # firebase_push_status PENDING -> SUCCESS.
        push_tutorial_to_firebase(tutorial_id=tutorial.pk)
        tutorial.refresh_from_db()
        assert tutorial.firebase_push_status_enum == FirebasePushStatusEnum.SUCCESS

        # PushB: the status-change push itself now runs. Before this fix, it would see
        # firebase_push_status == SUCCESS (not PENDING) and raise
        # TutorialValidationException.
        push_tutorial_to_firebase(tutorial_id=tutorial.pk)

        tutorial.refresh_from_db()
        assert tutorial.status_enum == Tutorial.Status.ARCHIVED
        assert tutorial.firebase_push_status_enum == FirebasePushStatusEnum.SUCCESS

        fb_tutorial = tutorial_ref.get()
        assert fb_tutorial["status"] != "archived"  # NOTE: tutorial firebase status is unrelated to Tutorial.Status

    def test_lock_contention_gives_up_after_max_retries(self):
        tutorial = self._build_published_tutorial()

        lock_key = CeleryLock.Key.TUTORIAL_PUSH_TO_FIREBASE.format(tutorial.pk)
        assert cache.add(lock_key, 1, 30)  # simulate another push currently holding the lock

        try:
            with pytest.raises(MaxRetriesExceededError):
                push_tutorial_to_firebase.apply(kwargs={"tutorial_id": tutorial.pk}, retries=5, throw=True)
        finally:
            cache.delete(lock_key)

        tutorial.refresh_from_db()
        assert tutorial.firebase_push_status_enum == FirebasePushStatusEnum.SUCCESS

    def test_lock_contention_retries_instead_of_dropping(self):
        tutorial = self._build_published_tutorial()

        lock_key = CeleryLock.Key.TUTORIAL_PUSH_TO_FIREBASE.format(tutorial.pk)
        assert cache.add(lock_key, 1, 30)  # simulate another push currently holding the lock

        try:
            with patch("apps.tutorial.tasks.current_task") as mock_current_task:
                mock_current_task.request.retries = 0
                mock_current_task.retry.side_effect = Exception("retry-requested")

                with self.assertRaisesMessage(Exception, "retry-requested"):
                    push_tutorial_to_firebase(tutorial_id=tutorial.pk)

                mock_current_task.retry.assert_called_once_with(countdown=1, max_retries=5)
        finally:
            cache.delete(lock_key)

        tutorial.refresh_from_db()
        assert tutorial.firebase_push_status_enum == FirebasePushStatusEnum.SUCCESS

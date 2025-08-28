import typing

from apps.contributor.factories import ContributorUserFactory, ContributorUserGroupFactory
from apps.contributor.models import ContributorUser
from apps.mapping.firebase.firebase import pull_results_from_firebase
from apps.mapping.models import (
    MappingSession,
    MappingSessionResult,
    MappingSessionResultTemp,
    MappingSessionUserGroup,
    MappingSessionUserGroupTemp,
)
from apps.project.factories import (
    OrganizationFactory,
    ProjectFactory,
    ProjectTaskFactory,
    ProjectTaskGroupFactory,
)
from apps.project.models import ProjectTypeEnum
from apps.user.factories import UserFactory
from main.config import Config
from main.tests import TestCase

FH = Config.FIREBASE_HELPER


class TestPullFromFirebase(TestCase):
    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory.create()

        cls.user_resource_kwargs = dict(
            created_by=cls.user,
            modified_by=cls.user,
        )

        cls.organization = OrganizationFactory.create(**cls.user_resource_kwargs)

        cls.project_common_kwargs = dict(
            **cls.user_resource_kwargs,
            project_number=1,
            requesting_organization=cls.organization,
            project_type_specifics={},
        )

        # Some init dummy projects
        cls.projects = [
            ProjectFactory.create(
                **cls.project_common_kwargs,
                topic=f"Test Topic {i}",
                region=f"Test Region {i}",
                project_type=project_type,
            )
            for i, project_type in enumerate(
                [
                    ProjectTypeEnum.FIND,
                    ProjectTypeEnum.COMPARE,
                    ProjectTypeEnum.COMPLETENESS,
                ],
            )
        ]

        cls._valid_data_common_kwargs = {
            "task_group_count": 10,
            "task_count": 5,
            "user_groups_to_map": 10,
            "users_to_map": 5,
        }

    def _valid_data(
        self,
        *,
        task_group_count: int,
        task_count: int,
        user_groups_to_map: int,
        users_to_map: int,
        override_data: dict[str, typing.Any] | None = None,
        invalid_data: bool = False,
        invalid_contributor_users: bool = False,
    ):
        project = ProjectFactory.create(
            **self.project_common_kwargs,
            topic="Test Topic Valid",
            region="Test Region Valid",
            project_type=ProjectTypeEnum.COMPLETENESS,
        )

        # Generate some data in db
        project_groups = ProjectTaskGroupFactory.create_batch(task_group_count, project=project)
        contributor_users = ContributorUserFactory.create_batch(users_to_map)
        contributor_user_groups = ContributorUserGroupFactory.create_batch(user_groups_to_map, **self.user_resource_kwargs)

        project_tasks_by_group = {}
        for project_task_group in project_groups:
            project_tasks_by_group[project_task_group.pk] = ProjectTaskFactory.create_batch(
                task_count,
                task_group=project_task_group,
            )

        ref_results = FH.ref(Config.FirebaseKeys.results_projects())

        mock_firebase_results_data = {
            # v2/results/
            project.firebase_id: {
                project_task_group.firebase_id: {
                    contributor_user.firebase_id: {
                        # Valid data
                        "startTime": "2025-08-05T10:04:38.933Z",
                        "endTime": "2025-08-05T11:04:38.933Z",
                        "appVersion": "0.2.8",
                        "ClientType": "web",
                        "userGroups": {
                            contributor_user_group.firebase_id: True for contributor_user_group in contributor_user_groups
                        },
                        "results": {
                            project_task.firebase_id: 1 for project_task in project_tasks_by_group[project_task_group.pk]
                        },
                        **(override_data or {}),
                    }
                    for contributor_user in [
                        *contributor_users,
                        *(
                            [
                                # Some non-referenceable dataset
                                ContributorUser(firebase_id="dummy-01"),
                                ContributorUser(firebase_id="dummy-02"),
                            ]
                            if invalid_contributor_users
                            else []
                        ),
                    ]
                }
                for project_task_group in project_groups
            },
        }

        ref_results.set(mock_firebase_results_data)

        assert [
            MappingSession.objects.count(),
            MappingSessionResult.objects.count(),
            MappingSessionUserGroup.objects.count(),
            MappingSessionUserGroupTemp.objects.count(),
            MappingSessionResultTemp.objects.count(),
        ] == [0, 0, 0, 0, 0]

        pull_results_from_firebase()

        if invalid_contributor_users:
            assert ref_results.get() is not None, "results should not be empty in the firebase"
            assert {
                contributor_user_fid
                for _, p_data in ref_results.get().items()  # pyright: ignore[reportAttributeAccessIssue]
                for _, g_data in p_data.items()
                for contributor_user_fid in g_data
            } == {"dummy-01", "dummy-02"}, "only dummy results should be in the firebase"
        else:
            assert ref_results.get() is None, "results should be cleared from the firebase"

        expected_mapping_sessions_count = task_group_count * users_to_map
        expected_mapping_sessions_user_groups_count = expected_mapping_sessions_count * user_groups_to_map
        expected_mapping_sessions_results_count = expected_mapping_sessions_count * task_count

        if invalid_data:
            expected_mapping_sessions_count = 0
            expected_mapping_sessions_user_groups_count = 0
            expected_mapping_sessions_results_count = 0

        assert [
            MappingSession.objects.count(),
            MappingSessionUserGroup.objects.count(),
            MappingSessionResult.objects.count(),
        ] == [
            expected_mapping_sessions_count,
            expected_mapping_sessions_user_groups_count,
            expected_mapping_sessions_results_count,
        ]

        # Temp tables
        assert [
            MappingSessionUserGroupTemp.objects.count(),
            MappingSessionResultTemp.objects.count(),
        ] == [0, 0]

    def _invalid_data(self, override_data: dict[str, typing.Any] | None = None):
        return self._valid_data(
            task_group_count=10,
            task_count=5,
            user_groups_to_map=10,
            users_to_map=5,
            invalid_data=True,
            override_data=override_data,
        )

    def test_valid_data_01(self):
        self._valid_data(
            task_group_count=5,
            task_count=10,
            user_groups_to_map=2,
            users_to_map=5,
        )

    def test_valid_data_02(self):
        self._valid_data(
            task_group_count=10,
            task_count=5,
            user_groups_to_map=2,
            users_to_map=5,
        )

    def test_valid_data_03(self):
        self._valid_data(
            task_group_count=5,
            task_count=10,
            user_groups_to_map=10,
            users_to_map=5,
        )

    def test_valid_data_04(self):
        self._valid_data(
            task_group_count=10,
            task_count=5,
            user_groups_to_map=10,
            users_to_map=5,
        )

    def test_invalid_data_01(self):
        self._invalid_data(
            override_data={
                # endTime < startTime
                "endTime": "2025-08-05T09:56:50.923Z",
                "startTime": "2025-08-05T10:04:38.933Z",
            },
        )

    def test_invalid_data_02(self):
        self._invalid_data(
            override_data={
                "results": "noop",
            },
        )

    def test_invalid_data_03(self):
        # TODO: Add more cases, for group?
        self._valid_data(
            task_group_count=5,
            task_count=10,
            user_groups_to_map=2,
            users_to_map=5,
            invalid_contributor_users=True,
        )

    # TODO: Handle handle this kind of data?
    # def test_invalid_data_03(self):
    #     self._invalid_data(
    #         override_data={
    #             "userGroups": "noop",
    #         },
    #     )

    # TODO: Add more cases?
    # - "userGroups": "noop",

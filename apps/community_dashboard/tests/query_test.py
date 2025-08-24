import datetime
import typing
from unittest import mock

from apps.community_dashboard.factories import AggregatedUserGroupStatDataFactory
from apps.community_dashboard.management.commands.update_aggregated_data import (
    Command as AggregateCommand,
)
from apps.contributor.factories import (
    ContributorUserFactory,
    ContributorUserGroupFactory,
    ContributorUserGroupMembershipFactory,
)
from apps.contributor.models import ContributorUser, ContributorUserGroup
from apps.mapping.factories import (
    MappingSessionFactory,
    MappingSessionResultFactory,
    MappingSessionUserGroupFactory,
)
from apps.project.factories import OrganizationFactory, ProjectFactory, ProjectTaskFactory, ProjectTaskGroupFactory
from apps.project.models import Project, ProjectTypeEnum
from apps.user.factories import UserFactory
from main.tests import TestCase
from project_types.base.project import BaseProject as BaseProjectHandler


class FakeBaseProjectHandler(typing.NamedTuple):
    project: Project

    def get_max_time_spend_percentile(self) -> float:
        return 11.2  # NOTE: value for COMPARE project_type


# TODO(thenav56): Validate data accuracy


class TestCommunityDashboardQuery(TestCase):
    @typing.override
    @classmethod
    def setUpTestData(cls):
        cls.now = datetime.datetime(
            year=2025,
            month=5,
            day=9,
            tzinfo=datetime.UTC,
        )
        base_datetime = cls.now - datetime.timedelta(days=1)

        cls.user = UserFactory.create()

        cls.ur_kwargs = dict(
            created_by=cls.user,
            modified_by=cls.user,
        )

        cls.organization = OrganizationFactory.create(**cls.ur_kwargs)
        cls.contributor_users = ContributorUserFactory.create_batch(10)

        # Project, Group, Task
        cls.pr_kwargs = dict(
            **cls.ur_kwargs,
            requesting_organization=cls.organization,
        )

        cls.project = ProjectFactory.create(**cls.pr_kwargs, project_type=ProjectTypeEnum.COMPARE)
        cls.project_groups = ProjectTaskGroupFactory.create_batch(4, project=cls.project)
        cls.project_tasks = [
            _task
            for _group in cls.project_groups
            for _task in ProjectTaskFactory.create_batch(
                4,
                task_group=_group,
            )
        ]

        old_mapping_session_datetime = base_datetime - datetime.timedelta(days=40)

        cls.mapping_sessions = {
            _project_group.pk: MappingSessionFactory.create(
                project_task_group=_project_group,
                contributor_user=contributor_user,
                start_time=old_mapping_session_datetime,
                end_time=old_mapping_session_datetime + datetime.timedelta(minutes=1),
                items_count=10,
            )
            for _project_group in cls.project_groups
            for contributor_user in cls.contributor_users[:5]
        }

        cls.mapping_sessions = {
            _project_group.pk: MappingSessionFactory.create(
                project_task_group=_project_group,
                contributor_user=contributor_user,
                start_time=base_datetime,
                end_time=base_datetime + datetime.timedelta(minutes=1),
                items_count=10,
            )
            for _project_group in cls.project_groups
            for contributor_user in cls.contributor_users[5:]
        }

        cls.results = {
            _value: [
                MappingSessionResultFactory.create(
                    session=cls.mapping_sessions.get(_project_task.task_group_id),
                    project_task_id=_project_task.pk,
                    result=_value,
                )
                for _project_task in _project_tasks
            ]
            for _value, _project_tasks in [
                (0, cls.project_tasks[:8]),
                (1, cls.project_tasks[8:]),
            ]
        }

        cls.contributor_user_groups = ContributorUserGroupFactory.create_batch(4, **cls.ur_kwargs)

        [
            MappingSessionUserGroupFactory(
                mapping_session_id=_mapping_session_id,
                user_group_id=_contributor_user_group_id,
            )
            for _contributor_user_groups, _results in [
                (cls.contributor_user_groups[:2], cls.results[0]),
                (cls.contributor_user_groups[3:], cls.results[1]),
            ]
            for _contributor_user_group_id, _mapping_session_id in set(
                [
                    (_contributor_user_group.pk, _result.session_id)
                    for _result in _results
                    for _contributor_user_group in _contributor_user_groups
                ],
            )
        ]

        # Run groups post-actions for the project using dummy project handler object with base
        BaseProjectHandler.analyze_groups(
            FakeBaseProjectHandler(project=cls.project),  # type: ignore[reportArgumentType]
        )
        AggregateCommand().run()

    @typing.override
    def setUp(self):
        super().setUp()
        timezone_now_patcher = mock.patch("django.utils.timezone.now")
        self.addCleanup(timezone_now_patcher.stop)
        self.timezone_now_patcher = timezone_now_patcher.start()  # type: ignore[reportUninitializedInstanceVariable]
        self.timezone_now_patcher.return_value = self.now

    def test_community_stats(self):
        query = """
            query MyQuery {
              communityStats {
                totalContributors
                totalSwipes
                totalUserGroups
              }
              communityStatsLatest {
                totalContributors
                totalSwipes
                totalUserGroups
              }
            }
        """

        resp = self.query_check(query)
        assert (
            dict(
                communityStats=dict(
                    totalContributors=10,
                    totalSwipes=400,
                    totalUserGroups=3,
                ),
                communityStatsLatest=dict(
                    totalContributors=5,
                    totalSwipes=200,
                    totalUserGroups=3,
                ),
            )
            == resp["data"]
        )

    def test_filtered_community_stats(self):
        query = """
          query FilteredCommunityStats($fromDate: Date!, $toDate: Date!) {
            communityFilteredStats(dateRange: {fromDate: $fromDate, toDate: $toDate}) {
              swipeByProjectGeo {
                geojson
                totalContribution
              }
              areaSwipedByProjectType {
                totalArea
                projectType
                projectTypeDisplay
              }
              swipeByProjectType {
                projectType
                totalSwipes
                projectTypeDisplay
              }
              swipeTimeByDate {
                date
                totalSwipeTime
              }
              swipeByOrganizationName {
                organizationName
                totalSwipes
              }
            }
          }
        """

        resp = self.query_check(
            query,
            variables={
                "fromDate": "2025-01-01",
                "toDate": "2025-05-31",
            },
        )
        assert resp["data"] == {
            "communityFilteredStats": {
                "areaSwipedByProjectType": [
                    {
                        "projectType": self.genum(self.project.project_type_enum),
                        "projectTypeDisplay": self.project.project_type_enum.label,
                        "totalArea": 0.0,
                    },
                ],
                "swipeByOrganizationName": [
                    {
                        "organizationName": self.organization.name,
                        "totalSwipes": 400,
                    },
                ],
                "swipeByProjectGeo": [
                    {
                        "geojson": {"coordinates": [1.0, 2.0], "type": "Point"},
                        "totalContribution": 400,
                    },
                ],
                "swipeByProjectType": [
                    {
                        "projectType": "COMPARE",
                        "projectTypeDisplay": "Compare",
                        "totalSwipes": 400,
                    },
                ],
                "swipeTimeByDate": [
                    {"date": "2025-03-29", "totalSwipeTime": 895},
                    {"date": "2025-05-08", "totalSwipeTime": 895},
                ],
            },
        }

    def test_user_group_aggregated_calc(self):
        query = """
            query MyQuery($userGroupId: ID!) {
              communityUserGroupStats(userGroupId: $userGroupId) {
                stats {
                  totalAreaSwiped
                  totalContributors
                  totalMappingProjects
                  totalOrganization
                  totalSwipeTime
                  totalSwipes
                }
              }
            }
        """

        without_data = dict(
            totalAreaSwiped=0,
            totalContributors=0,
            totalMappingProjects=0,
            totalOrganization=0,
            totalSwipeTime=0,
            totalSwipes=0,
        )

        with_data = dict(
            totalAreaSwiped=0,
            totalContributors=1,
            totalMappingProjects=1,
            totalOrganization=1,
            totalSwipeTime=90,
            totalSwipes=20,
        )

        resp_map = {}
        for contributor_user_group in self.contributor_user_groups:
            resp = self.query_check(
                query,
                variables=dict(
                    userGroupId=contributor_user_group.pk,
                ),
            )
            resp_map[contributor_user_group.pk] = resp["data"]["communityUserGroupStats"]["stats"]

        assert {
            contributor_user_group.pk: (without_data if index == 2 else with_data)
            for index, contributor_user_group in enumerate(self.contributor_user_groups)
        } == resp_map

    # TODO(thenav56): Add filters and aggregations as well
    def test_user_group_query(self):
        query = """
            query MyQuery($userGroupId: ID!, $pagination: OffsetPaginationInput!) {
              contributorUserGroup(id: $userGroupId) {
                id
                name
                createdAt
                archivedAt
                isArchived
              }
              contributorUserGroupMembers(
                  filters: {
                      userGroupId: {
                          exact: $userGroupId,
                      },
                  },
                  pagination: $pagination,
              ) {
                totalCount
                pageInfo {
                  limit
                  offset
                }
                results {
                  isActive
                  totalMappingProjects
                  totalSwipeTime
                  totalSwipes
                  user {
                    id
                    firebaseId
                    username
                  }
                }
              }
            }
        """

        project = ProjectFactory.create(**self.pr_kwargs, project_type=ProjectTypeEnum.FIND)
        contributor_user_group = ContributorUserGroupFactory.create(**self.ur_kwargs)
        contributor_users = ContributorUserFactory.create_batch(4)

        # Create some memberships
        for index, user in enumerate(contributor_users, start=1):
            if index <= 3:
                ContributorUserGroupMembershipFactory.create(
                    user_group=contributor_user_group,
                    user=user,
                )
            AggregatedUserGroupStatDataFactory.create(
                project=project,
                user=user,
                user_group=contributor_user_group,
                timestamp_date="2020-01-01",
                total_time=10 * index,
                task_count=(10 + 1) * index,
                swipes=(10 + 2) * index,
                area_swiped=(10 + 3) * index,
            )

        def _get_user_data(user: ContributorUser):
            return {
                "id": self.gID(user.pk),
                "firebaseId": user.firebase_id,
                "username": user.username,
            }

        for offset, expected_memberships in [
            (
                0,
                [
                    {
                        "isActive": True,
                        "totalMappingProjects": 1,
                        "totalSwipeTime": 10,
                        "totalSwipes": 12,
                        "user": _get_user_data(contributor_users[0]),
                    },
                    {
                        "isActive": True,
                        "totalMappingProjects": 1,
                        "totalSwipeTime": 20,
                        "totalSwipes": 24,
                        "user": _get_user_data(contributor_users[1]),
                    },
                ],
            ),
            (
                2,
                [
                    {
                        "isActive": True,
                        "totalMappingProjects": 1,
                        "totalSwipeTime": 30,
                        "totalSwipes": 36,
                        "user": _get_user_data(contributor_users[2]),
                    },
                ],
            ),
        ]:
            resp = self.query_check(
                query,
                variables=dict(
                    userGroupId=contributor_user_group.pk,
                    pagination=dict(
                        limit=2,
                        offset=offset,
                    ),
                ),
            )
            assert {
                "data": {
                    "contributorUserGroup": {
                        "id": self.gID(contributor_user_group.pk),
                        "name": contributor_user_group.name,
                        "archivedAt": self.gdatetime(contributor_user_group.archived_at),
                        "createdAt": self.gdatetime(contributor_user_group.created_at),
                        "isArchived": contributor_user_group.is_archived,
                    },
                    "contributorUserGroupMembers": {
                        "totalCount": 3,
                        "pageInfo": {
                            "limit": 2,
                            "offset": offset,
                        },
                        "results": expected_memberships,
                    },
                },
            } == resp

    def test_user_groups_query(self):
        query = """
          query MyQuery($pagination: OffsetPaginationInput!) {
            contributorUserGroups(
                pagination: $pagination,
                order: {id: ASC},
            ) {
              totalCount
              pageInfo {
                limit
                offset
              }
              results {
                id
                name
                createdAt
                archivedAt
                isArchived
              }
            }
          }
        """

        existing_contributor_user_groups_count = ContributorUserGroup.objects.count()
        # NOTE: ContributorUserGroup with empty name should be filtered out. They aren't sync yet
        ContributorUserGroupFactory.create_batch(3, **self.ur_kwargs, name="")

        offset = 0
        resp = self.query_check(
            query,
            variables=dict(
                pagination=dict(
                    limit=2,
                    offset=offset,
                ),
            ),
        )

        assert {
            "data": {
                "contributorUserGroups": {
                    "totalCount": existing_contributor_user_groups_count,
                    "pageInfo": {
                        "limit": 2,
                        "offset": offset,
                    },
                    "results": [
                        {
                            "id": self.gID(contributor_user_group.id),
                            "name": contributor_user_group.name,
                            "archivedAt": self.gdatetime(contributor_user_group.archived_at),
                            "createdAt": self.gdatetime(contributor_user_group.created_at),
                            "isArchived": contributor_user_group.is_archived,
                        }
                        for contributor_user_group in self.contributor_user_groups[:2]
                    ],
                },
            },
        } == resp

    def test_user_query(self):
        query = """
          query MyQuery(
              $firebaseId: ID!,
              $pagination: OffsetPaginationInput!,
              $fromDate: Date!,
              $toDate: Date!,
          ) {

            contributorUserByFirebaseId(firebaseId: $firebaseId) {
              id
              firebaseId
              username
            }

            communityUserStats(firebaseId: $firebaseId) {
              id
              stats {
                totalSwipes
                totalSwipeTime
              }
              statsLatest {
                totalSwipes
                totalSwipeTime
                totalUserGroups
              }

              filteredStats(dateRange: {fromDate: $fromDate, toDate: $toDate}) {
                id
                areaSwipedByProjectType {
                  totalArea
                  projectType
                  projectTypeDisplay
                }
                swipeByProjectGeo {
                  geojson
                  totalContribution
                }
                swipeByDate {
                  taskDate
                  totalSwipes
                }
                swipeByOrganizationName {
                  organizationName
                  totalSwipes
                }
                swipeByProjectType {
                  projectType
                  projectTypeDisplay
                  totalSwipes
                }
                swipeTimeByDate {
                  date
                  totalSwipeTime
                }
              }

            }

            contributorUserGroups(
                filters: {
                  userFirebaseId: $firebaseId,
                },
                pagination: $pagination,
                order: {id: ASC},
            ) {
              totalCount
              pageInfo {
                limit
                offset
              }
              results {
                id
                name
                membersCount
              }
            }

          }
        """

        project = ProjectFactory.create(**self.pr_kwargs)
        contributor_user = self.contributor_users[0]
        additional_contributor_users = ContributorUserFactory.create_batch(3)
        contributor_user_groups = ContributorUserGroupFactory.create_batch(4, **self.ur_kwargs)

        # Create some memberships
        for index, contributor_user_group in enumerate(contributor_user_groups, start=1):
            if index <= 3:
                ContributorUserGroupMembershipFactory.create(
                    user_group=contributor_user_group,
                    user=contributor_user,
                )
            # Additional users
            for additional_user in additional_contributor_users[:index]:
                ContributorUserGroupMembershipFactory.create(
                    user_group=contributor_user_group,
                    user=additional_user,
                )
            AggregatedUserGroupStatDataFactory.create(
                project=project,
                user=contributor_user,
                user_group=contributor_user_group,
                timestamp_date="2020-01-01",
                total_time=10 * index,
                task_count=(10 + 1) * index,
                swipes=(10 + 2) * index,
                area_swiped=(10 + 3) * index,
            )

        for offset, expected_memberships in [
            (
                0,
                [
                    {
                        "id": self.gID(contributor_user_groups[0].pk),
                        "name": contributor_user_groups[0].name,
                        "membersCount": 2,
                    },
                    {
                        "id": self.gID(contributor_user_groups[1].pk),
                        "name": contributor_user_groups[1].name,
                        "membersCount": 3,
                    },
                ],
            ),
            (
                2,
                [
                    {
                        "id": self.gID(contributor_user_groups[2].pk),
                        "name": contributor_user_groups[2].name,
                        "membersCount": 4,
                    },
                ],
            ),
        ]:
            resp = self.query_check(
                query,
                variables=dict(
                    firebaseId=contributor_user.firebase_id,
                    pagination=dict(
                        limit=2,
                        offset=offset,
                    ),
                    fromDate="2025-01-01",
                    toDate="2025-05-31",
                ),
            )

            assert {
                "contributorUserByFirebaseId": {
                    "id": self.gID(contributor_user.pk),
                    "firebaseId": contributor_user.firebase_id,
                    "username": contributor_user.username,
                },
                "communityUserStats": {
                    "id": self.gID(contributor_user.pk),
                    "stats": {
                        "totalSwipeTime": 179,
                        "totalSwipes": 40,
                    },
                    "statsLatest": {
                        "totalSwipeTime": 0,
                        "totalSwipes": 0,
                        "totalUserGroups": 4,
                    },
                    "filteredStats": {
                        "id": self.gID(contributor_user.pk),
                        "areaSwipedByProjectType": [
                            {
                                "projectType": self.genum(self.project.project_type_enum),
                                "projectTypeDisplay": self.project.project_type_enum.label,
                                "totalArea": 0.0,
                            },
                        ],
                        "swipeByDate": [
                            {
                                "taskDate": "2025-03-29",
                                "totalSwipes": 40,
                            },
                        ],
                        "swipeByOrganizationName": [
                            {
                                "organizationName": self.organization.name,
                                "totalSwipes": 40,
                            },
                        ],
                        "swipeByProjectGeo": [
                            {
                                "geojson": {
                                    "coordinates": [1.0, 2.0],
                                    "type": "Point",
                                },
                                "totalContribution": 40,
                            },
                        ],
                        "swipeByProjectType": [
                            {
                                "projectType": self.genum(self.project.project_type_enum),
                                "projectTypeDisplay": self.project.project_type_enum.label,
                                "totalSwipes": 40,
                            },
                        ],
                        "swipeTimeByDate": [
                            {
                                "date": "2025-03-29",
                                "totalSwipeTime": 179,
                            },
                        ],
                    },
                },
                "contributorUserGroups": {
                    "totalCount": 3,
                    "pageInfo": {
                        "limit": 2,
                        "offset": offset,
                    },
                    "results": expected_memberships,
                },
            } == resp["data"]

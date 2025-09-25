import typing

from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.project.models import ProjectStatusEnum, ProjectTypeEnum
from apps.user.factories import UserFactory
from main.tests import TestCase


class TestProjectFiltersAndOrders(TestCase):
    class Query:
        PROJECTS_WITH_FILTERS = """
            query Projects(
                $pagination: OffsetPaginationInput,
                $filters: ProjectFilter,
                $order: ProjectOrder,
                $includeAll: Boolean
            ) {
              projects(pagination: $pagination, filters: $filters, order: $order, includeAll: $includeAll) {
                totalCount
                pageInfo {
                  offset
                  limit
                }
                results {
                  id
                  name
                  topic
                  projectType
                  requestingOrganization {
                    id
                    name
                  }
                  isFeatured
                  status
                  lookFor
                }
              }
            }
        """

    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory.create()
        cls.user_resource_kwargs = dict(
            created_by=cls.user,
            modified_by=cls.user,
        )

        cls.organization1 = OrganizationFactory.create(**cls.user_resource_kwargs)
        cls.organization2 = OrganizationFactory.create(**cls.user_resource_kwargs)

        cls.find_project = ProjectFactory.create(
            **cls.user_resource_kwargs,
            topic="Find Project Alpha",
            requesting_organization=cls.organization1,
            project_type=ProjectTypeEnum.FIND,
            is_featured=True,
            status=ProjectStatusEnum.PROCESSED,
            look_for="buildings",
        )

        cls.compare_project = ProjectFactory.create(
            **cls.user_resource_kwargs,
            topic="Compare Project Beta",
            requesting_organization=cls.organization1,
            project_type=ProjectTypeEnum.COMPARE,
            is_featured=False,
            status=ProjectStatusEnum.PROCESSED,
            look_for="roads",
        )

        cls.completeness_project = ProjectFactory.create(
            **cls.user_resource_kwargs,
            topic="Completeness Project Gamma",
            requesting_organization=cls.organization2,
            project_type=ProjectTypeEnum.COMPLETENESS,
            is_featured=True,
            status=ProjectStatusEnum.PROCESSED,
            look_for="buildings",
        )

        cls.find_project_2 = ProjectFactory.create(
            **cls.user_resource_kwargs,
            topic="Find Project Delta",
            requesting_organization=cls.organization2,
            project_type=ProjectTypeEnum.FIND,
            is_featured=False,
            status=ProjectStatusEnum.READY_TO_PROCESS,
            look_for="water",
        )

        cls.withdrawn_project = ProjectFactory.create(
            **cls.user_resource_kwargs,
            topic="Withdrawn Project",
            requesting_organization=cls.organization2,
            project_type=ProjectTypeEnum.VALIDATE,
            is_featured=False,
            status=ProjectStatusEnum.WITHDRAWN,
            look_for="water",
        )

    def _query(
        self,
        filters: dict[str, typing.Any] | None = None,
        order: dict[str, str] | None = None,
    ):
        return self.query_check(
            self.Query.PROJECTS_WITH_FILTERS,
            variables={
                "includeAll": True,
                "pagination": {
                    "limit": 10,
                    "offset": 0,
                },
                "filters": filters or {},
                "order": order or {},
            },
        )

    def test_filter_by_id(self):
        self.force_login(self.user)
        content = self._query(
            filters={
                "id": {"exact": self.gID(self.find_project.pk)},
            },
        )
        assert content["data"]["projects"]["totalCount"] == 1
        assert content["data"]["projects"]["results"][0]["id"] == self.gID(self.find_project.pk)

    def test_filter_by_name(self):
        self.force_login(self.user)
        content = self._query(
            filters={
                "name": "Find Project Alpha",
            },
        )
        assert content["data"]["projects"]["totalCount"] == 1
        assert content["data"]["projects"]["results"][0]["id"] == self.gID(self.find_project.id)
        content = self._query(
            filters={
                "name": "project",
            },
        )
        assert content["data"]["projects"]["totalCount"] == 5

    def test_filter_by_project_type(self):
        self.force_login(self.user)
        content = self._query(
            filters={
                "projectType": {"exact": self.genum(ProjectTypeEnum.FIND)},
            },
        )
        assert content["data"]["projects"]["totalCount"] == 2

    def test_filter_by_status(self):
        self.force_login(self.user)
        content = self._query(
            filters={
                "status": {"exact": self.genum(ProjectStatusEnum.PROCESSED)},
            },
        )
        assert content["data"]["projects"]["totalCount"] == 3

        content = self._query(
            filters={
                "status": {"exact": self.genum(ProjectStatusEnum.WITHDRAWN)},
            },
        )
        assert content["data"]["projects"]["totalCount"] == 1

    def test_ordering_by_topic(self):
        self.force_login(self.user)
        content = self._query(
            order={
                "topic": "ASC",
            },
        )
        assert [project["topic"] for project in content["data"]["projects"]["results"]] == [
            self.compare_project.topic,
            self.completeness_project.topic,
            self.find_project.topic,
            self.find_project_2.topic,
            self.withdrawn_project.topic,
        ]

    def test_ordering_by_id(self):
        self.force_login(self.user)
        content = self._query(
            order={
                "id": "DESC",
            },
        )
        assert [project["id"] for project in content["data"]["projects"]["results"]] == [
            self.gID(self.withdrawn_project.pk),
            self.gID(self.find_project_2.pk),
            self.gID(self.completeness_project.pk),
            self.gID(self.compare_project.pk),
            self.gID(self.find_project.pk),
        ]

    def test_ordering_by_name(self):
        self.force_login(self.user)

        # Ascending order by name
        content = self._query(
            order={
                "name": "ASC",
            },
        )
        assert sorted([project["name"] for project in content["data"]["projects"]["results"]]) == sorted(
            [
                self.compare_project.generate_name(),
                self.completeness_project.generate_name(),
                self.find_project.generate_name(),
                self.find_project_2.generate_name(),
                self.withdrawn_project.generate_name(),
            ],
        )

        # Descending order by name
        content = self._query(
            order={
                "name": "DESC",
            },
        )
        assert sorted([project["name"] for project in content["data"]["projects"]["results"]]) == sorted(
            [
                self.withdrawn_project.generate_name(),
                self.find_project_2.generate_name(),
                self.find_project.generate_name(),
                self.completeness_project.generate_name(),
                self.compare_project.generate_name(),
            ],
        )

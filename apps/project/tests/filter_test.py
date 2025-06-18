import typing

from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.project.models import ProjectStatusEnum, ProjectTypeEnum
from apps.user.factories import UserFactory
from main.tests import TestCase


class TestProjectFiltersAndOrders(TestCase):
    class Query:
        PROJECTS_WITH_FILTERS = """
            query Projects($pagination: OffsetPaginationInput, $filters: ProjectFilter, $order: ProjectOrder) {
              projects(pagination: $pagination, filters: $filters, order: $order) {
                totalCount
                pageInfo {
                  offset
                  limit
                }
                results {
                  id
                  name
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
            name="Find Project Alpha",
            requesting_organization=cls.organization1,
            project_type=ProjectTypeEnum.FIND,
            is_featured=True,
            status=ProjectStatusEnum.READY,
            look_for="buildings",
        )

        cls.compare_project = ProjectFactory.create(
            **cls.user_resource_kwargs,
            name="Compare Project Beta",
            requesting_organization=cls.organization1,
            project_type=ProjectTypeEnum.COMPARE,
            is_featured=False,
            status=ProjectStatusEnum.READY,
            look_for="roads",
        )

        cls.completeness_project = ProjectFactory.create(
            **cls.user_resource_kwargs,
            name="Completeness Project Gamma",
            requesting_organization=cls.organization2,
            project_type=ProjectTypeEnum.COMPLETENESS,
            is_featured=True,
            status=ProjectStatusEnum.READY,
            look_for="buildings",
        )

        cls.find_project_2 = ProjectFactory.create(
            **cls.user_resource_kwargs,
            name="Find Project Delta",
            requesting_organization=cls.organization2,
            project_type=ProjectTypeEnum.FIND,
            is_featured=False,
            status=ProjectStatusEnum.MARKED_AS_READY,
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
                "name": {"iContains": "Find Project Alpha"},
            },
        )
        assert content["data"]["projects"]["totalCount"] == 1
        assert content["data"]["projects"]["results"][0]["name"] == self.find_project.name
        content = self._query(
            filters={
                "name": {"iContains": "project"},
            },
        )
        assert content["data"]["projects"]["totalCount"] == 4

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
                "status": {"exact": self.genum(ProjectStatusEnum.READY)},
            },
        )
        assert content["data"]["projects"]["totalCount"] == 3

    def test_ordering_by_name(self):
        self.force_login(self.user)
        content = self._query(
            order={
                "name": "ASC",
            },
        )
        assert [project["name"] for project in content["data"]["projects"]["results"]] == [
            self.compare_project.name,
            self.completeness_project.name,
            self.find_project.name,
            self.find_project_2.name,
        ]

    def test_orderring_by_id(self):
        self.force_login(self.user)
        content = self._query(
            order={
                "id": "DESC",
            },
        )
        assert [project["id"] for project in content["data"]["projects"]["results"]] == [
            self.gID(self.find_project_2.pk),
            self.gID(self.completeness_project.pk),
            self.gID(self.compare_project.pk),
            self.gID(self.find_project.pk),
        ]

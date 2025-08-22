import typing

from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.project.models import (
    ProjectTypeEnum,
)
from apps.tutorial.factories import (
    TutorialFactory,
)
from apps.tutorial.models import (
    TutorialStatusEnum,
)
from apps.user.factories import UserFactory
from main.tests import TestCase


class TestTutorialFilterQuery(TestCase):
    class Query:
        TUTORIALS_WITH_FILTERS = """
            query Tutorials($pagination: OffsetPaginationInput, $filters: TutorialFilter, $includeAll: Boolean) {
              tutorials(pagination: $pagination, filters: $filters, includeAll: $includeAll) {
                totalCount
                pageInfo {
                  offset
                  limit
                }
                results {
                  id
                  clientId
                  name
                  status
                  projectId
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

        cls.organization = OrganizationFactory.create(**cls.user_resource_kwargs)

        cls.project1, cls.project2, cls.project3 = ProjectFactory.create_batch(
            3,
            **cls.user_resource_kwargs,
            project_type=ProjectTypeEnum.FIND,
            requesting_organization=cls.organization,
            topic="New Project",
            look_for="buildings",
            additional_info_url="https://hi-there/about.html",
            description="The new **project** from hi-there.",
        )
        # Creating tutorials
        cls.tutorial1 = TutorialFactory.create(
            **cls.user_resource_kwargs,
            project=cls.project1,
            name="First Tutorial",
            status=TutorialStatusEnum.DRAFT,
        )
        cls.tutorial2 = TutorialFactory.create(
            **cls.user_resource_kwargs,
            project=cls.project2,
            name="Second Tutorial",
            status=TutorialStatusEnum.PUBLISHED,
        )
        cls.tutorial3 = TutorialFactory.create(
            **cls.user_resource_kwargs,
            project=cls.project3,
            name="Third Tutorial",
            status=TutorialStatusEnum.ARCHIVED,
        )

    def _query(
        self,
        filters: dict[str, typing.Any] | None = None,
        order: dict[str, str] | None = None,
    ):
        return self.query_check(
            self.Query.TUTORIALS_WITH_FILTERS,
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
                "id": {"exact": self.gID(self.tutorial1.id)},
            },
        )
        assert content["data"]["tutorials"]["totalCount"] == 1
        assert content["data"]["tutorials"]["results"][0]["id"] == self.gID(self.tutorial1.id)
        assert content["data"]["tutorials"]["results"][0]["projectId"] == self.gID(self.project1.id)

    def test_filter_by_name(self):
        self.force_login(self.user)
        content = self._query(
            filters={
                "name": "Tutorial",
            },
        )
        assert content["data"]["tutorials"]["totalCount"] == 3

        content = self._query(
            filters={
                "name": self.tutorial1.name,
            },
        )
        assert content["data"]["tutorials"]["totalCount"] == 1
        assert content["data"]["tutorials"]["results"][0]["name"] == self.tutorial1.name

    def test_filter_by_status(self):
        self.force_login(self.user)
        content = self._query(
            filters={
                "status": {"exact": self.genum(TutorialStatusEnum.DRAFT)},
            },
        )
        assert content["data"]["tutorials"]["totalCount"] == 1
        assert content["data"]["tutorials"]["results"][0]["id"] == self.gID(self.tutorial1.id)

        content = self._query(
            filters={
                "status": {
                    "inList": [self.genum(TutorialStatusEnum.PUBLISHED), self.genum(TutorialStatusEnum.ARCHIVED)],
                },
            },
        )
        assert content["data"]["tutorials"]["totalCount"] == 2
        assert len(content["data"]["tutorials"]["results"]) == 2
        assert all(
            result["status"] in [TutorialStatusEnum.PUBLISHED.name, TutorialStatusEnum.ARCHIVED.name]
            for result in content["data"]["tutorials"]["results"]
        ), content["data"]["tutorials"]["results"]

    def test_filter_by_project_type(self):
        self.force_login(self.user)
        content = self._query(
            filters={
                "project": {
                    "projectType": {"exact": self.genum(ProjectTypeEnum.FIND)},
                },
            },
        )
        assert content["data"]["tutorials"]["totalCount"] == 3
        assert all(
            result["projectId"] in [self.gID(self.project1.id), self.gID(self.project2.id), self.gID(self.project3.id)]
            for result in content["data"]["tutorials"]["results"]
        )

    def test_order_by_id(self):
        self.force_login(self.user)
        content = self._query(
            order={
                "id": "ASC",
            },
        )
        assert [result["id"] for result in content["data"]["tutorials"]["results"]] == [
            self.gID(self.tutorial3.id),
            self.gID(self.tutorial2.id),
            self.gID(self.tutorial1.id),
        ]

    def test_order_by_name(self):
        self.force_login(self.user)
        content = self._query(
            order={
                "name": "ASC",
            },
        )
        assert [result["name"] for result in content["data"]["tutorials"]["results"]] == [
            self.tutorial3.name,
            self.tutorial2.name,
            self.tutorial1.name,
        ]

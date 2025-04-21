import typing

from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.user.factories import UserFactory
from main.tests import TestCase


class TestProjectQuery(TestCase):
    class Query:
        PROJECTS = """
            query Projects($pagination: OffsetPaginationInput) {
              projects(order: {id: ASC}, pagination: $pagination) {
                totalCount
                pageInfo {
                  offset
                  limit
                }
                results {
                  id
                  name
                  projectType
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
        # Some init projects
        cls.projects = ProjectFactory.create_batch(
            3,
            **cls.user_resource_kwargs,
            requesting_organization=cls.organization,
        )

    def test_projects(self):
        def _query():
            return self.query_check(
                self.Query.PROJECTS,
                variables={
                    "pagination": {
                        "limit": 10,
                        "offset": 0,
                    },
                },
            )

        # Without authentication -----
        content = _query()
        assert content["data"]["projects"] == {
            **self.g_pagination(offset=0, limit=10, total_count=0, results=[]),
        }, content

        # With authentication -----
        self.force_login(self.user)
        content = _query()
        assert content["data"]["projects"] == {
            **self.g_pagination(
                offset=0,
                limit=10,
                total_count=3,
                results=[
                    dict(
                        id=self.gID(project.id),
                        name=project.name,
                        projectType=self.genum(project.project_type),
                    )
                    for project in self.projects
                ],
            ),
        }, content

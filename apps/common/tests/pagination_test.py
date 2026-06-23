import typing
from unittest.mock import patch

from strawberry_django.settings import DEFAULT_DJANGO_SETTINGS

from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.project.models import ProjectStatusEnum
from apps.user.factories import UserFactory
from main.tests import TestCase

_MAX_LIMIT = 5


def _patched_settings():
    return {**DEFAULT_DJANGO_SETTINGS, "PAGINATION_MAX_LIMIT": _MAX_LIMIT}


QUERY_WITH_PAGINATION = """
    query($pagination: OffsetPaginationInput) {
        publicProjects(pagination: $pagination) {
            totalCount
            pageInfo {
                limit
                offset
            }
            results {
                id
            }
        }
    }
"""

QUERY_NO_PAGINATION = """
    query {
        publicProjects {
            totalCount
            results {
                id
            }
        }
    }
"""


@patch("strawberry_django.pagination.strawberry_django_settings", _patched_settings)
class TestPaginationMaxLimit(TestCase):
    """Verify that PAGINATION_MAX_LIMIT is enforced on paginated endpoints."""

    @classmethod
    @typing.override
    def setUpTestData(cls):
        user = UserFactory.create()
        user_resource_kwargs = dict(
            created_by=user,
            modified_by=user,
        )
        organization = OrganizationFactory.create(**user_resource_kwargs)
        ProjectFactory.create_batch(
            7,
            status=ProjectStatusEnum.PUBLISHED,
            requesting_organization=organization,
            **user_resource_kwargs,
        )

    def test_limit_above_max_is_capped(self):
        resp = self.query_check(QUERY_WITH_PAGINATION, variables={"pagination": {"limit": 10, "offset": 0}})
        data = resp["data"]["publicProjects"]
        assert data["totalCount"] == 7
        assert len(data["results"]) == _MAX_LIMIT

    def test_limit_at_max_is_accepted(self):
        resp = self.query_check(QUERY_WITH_PAGINATION, variables={"pagination": {"limit": _MAX_LIMIT, "offset": 0}})
        data = resp["data"]["publicProjects"]
        assert data["pageInfo"]["limit"] == _MAX_LIMIT
        assert len(data["results"]) == _MAX_LIMIT

    def test_limit_below_max_is_unchanged(self):
        resp = self.query_check(QUERY_WITH_PAGINATION, variables={"pagination": {"limit": 3, "offset": 0}})
        data = resp["data"]["publicProjects"]
        assert data["pageInfo"]["limit"] == 3
        assert len(data["results"]) == 3

    def test_no_pagination_uses_default_limit(self):
        resp = self.query_check(QUERY_NO_PAGINATION)
        data = resp["data"]["publicProjects"]
        assert data["totalCount"] == 7
        assert len(data["results"]) == _MAX_LIMIT

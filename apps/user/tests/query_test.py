import typing

from apps.user.factories import UserFactory
from main.tests import TestCase


class TestUserQuery(TestCase):
    class Query:
        ME = """
            query meQuery {
              me {
                id
                email
                firstName
                lastName
                displayName
              }
            }
        """

        USERS = """
            query usersQuery {
              users(pagination: {limit: 10}) {
                totalCount
                pageInfo {
                  limit
                  offset
                }
                results {
                  id
                  lastName
                  firstName
                  displayName
                  anonymizeEmail
                }
              }
            }
        """

    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory.create(email="main-user@test.com")
        # Some other users as well
        cls.users = (
            UserFactory.create(first_name="Test", last_name="Hero", email="sample@test.com"),
            UserFactory.create(first_name="Example", last_name="Villain", email="sample@vil.com"),
            UserFactory.create(first_name="Test", last_name="Hero", email="hero-user@sample.com"),
        )
        # Inactive users (For noise)
        cls.inactive_users = [
            UserFactory.create(first_name="Inactive", last_name="Hero", email="inactive-user@sample.com", is_active=False),
        ]

    def test_me(self):
        # Without authentication -----
        content = self.query_check(self.Query.ME)
        assert content["data"]["me"] is None

        user = self.user
        # With authentication -----
        self.force_login(user)
        content = self.query_check(self.Query.ME)
        assert content["data"]["me"] == dict(
            id=self.gID(user.pk),
            email=user.email,
            firstName=user.first_name,
            lastName=user.last_name,
            displayName=f"{user.first_name} {user.last_name}",
        )

    def test_users(self):
        all_users = [self.user, *self.users]
        # Without authentication -----
        content = self.query_check(self.Query.USERS)
        assert content["data"]["users"] == {
            "pageInfo": {
                "limit": 10,
                "offset": 0,
            },
            "results": [],
            "totalCount": 0,
        }

        expected_anonymize_email_map = {
            "sample@test.com": "s***e@test.com",
            "sample@vil.com": "s***e@vil.com",
            "hero-user@sample.com": "h***r@sample.com",
            "main-user@test.com": "m***r@test.com",
        }

        user = self.user
        # With authentication -----
        self.force_login(user)
        content = self.query_check(self.Query.USERS)
        assert content["data"]["users"] == {
            "totalCount": len(all_users),
            "pageInfo": {
                "limit": 10,
                "offset": 0,
            },
            "results": [
                dict(
                    id=self.gID(_user.pk),
                    firstName=_user.first_name,
                    lastName=_user.last_name,
                    displayName=f"{_user.first_name} {_user.last_name}",
                    anonymizeEmail=expected_anonymize_email_map[_user.email],
                )
                for _user in all_users
            ],
        }

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

    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory.create()
        # Some other users as well
        cls.users = (
            UserFactory.create(first_name="Test", last_name="Hero", email="sample@test.com"),
            UserFactory.create(first_name="Example", last_name="Villain", email="sample@vil.com"),
            UserFactory.create(first_name="Test", last_name="Hero"),
        )

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

from django.test import TestCase


class FakeTest(TestCase):
    """Test for running migrations only.

    docker-compose run --rm server ./manage.py test -v 2 --pattern="main/tests/test_fake.py"
    """

    def test_fake(self):
        pass

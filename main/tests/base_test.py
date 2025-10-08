import logging
import typing
import warnings
from datetime import datetime
from enum import Enum

from django.conf import settings
from django.db import models
from django.test import TestCase as BaseTestCase
from django.test import override_settings

from main.config import Config

logger = logging.getLogger(__name__)

TEST_CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": settings.TEST_CACHE_REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "test_dj_cache-",
    },
    "local-memory": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
}

FILE_SYSTEM_TEST_STORAGES_CONFIGS = dict(
    AWS_S3_ENABLED=False,
    STORAGES={
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    },
)


@override_settings(
    DEBUG=True,
    EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend",
    MEDIA_ROOT="rest-media-temp",
    STORAGES=FILE_SYSTEM_TEST_STORAGES_CONFIGS["STORAGES"],
    CACHES=TEST_CACHES,
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    SLACK_BOT_ENABLED=False,
    SLACK_FALLBACK_TO_CONSOLE=True,
)
class TestCase(BaseTestCase):
    @typing.override
    def setUp(self):
        from django.core.cache import cache

        # Clear all test cache
        logger.info("Clearing cache")
        cache.clear()

        # Clear firebase data
        logger.info("Clearing firebase database")
        self.clear_firebase_data()
        self.firebase_helper = Config.FIREBASE_HELPER  # type: ignore[reportUninitializedInstanceVariable]

        super().setUp()

    def clear_firebase_data(self):
        assert Config.FIREBASE_EMULATOR_USE is True, "Cannot reset firebase because emulator is not used"
        assert Config.FIREBASE_EMULATOR_TEST_HOST is not None, "Cannot reset firebase without defining a whitelist"
        assert Config.FIREBASE_EMULATOR_HOST == Config.FIREBASE_EMULATOR_TEST_HOST, (
            "Cannot reset firebase because host is not whitelisted"
        )

        ref = Config.FIREBASE_HELPER.ref(Config.FirebaseKeys.v2())
        ref.delete()

    def force_login(self, user):  # type: ignore[reportMissingParameterType]
        self.client.force_login(user)

    def logout(self):
        self.client.logout()

    def query_check(
        self,
        query: str,
        assert_errors: bool = False,
        variables: dict[typing.Any, typing.Any] | None = None,
        files: dict[typing.Any, typing.Any] | None = None,
        **kwargs,  # type: ignore[reportMissingParameterType]
    ) -> dict[typing.Any, typing.Any]:
        import json

        if files:
            # Request type: form data
            response = self.client.post(
                "/graphql/",
                data={
                    "operations": json.dumps(
                        {
                            "query": query,
                            "variables": variables,
                        },
                    ),
                    **files,
                    "map": json.dumps(kwargs.pop("map")),
                },
                **kwargs,
            )
        else:
            # Request type: json
            response = self.client.post(
                "/graphql/",
                data={
                    "query": query,
                    "variables": variables,
                },
                content_type="application/json",
                **kwargs,
            )
        if assert_errors:
            self.assertResponseHasErrors(response)
        else:
            self.assertResponseNoErrors(response)
        return response.json()

    def assertWarning(self, condition: bool, msg: str):
        """Custom assertion that warns instead of failing the test."""
        if not condition:
            warning_message = msg or "Assertion warning: condition not met."
            warnings.warn(warning_message, stacklevel=2)

    def assertResponseNoErrors(self, resp: typing.Any, msg=None):  # type: ignore[reportMissingParameterType]
        """Assert that the call went through correctly. 200 means the syntax is ok,
        if there are no `errors`, the call was fine.

        :resp HttpResponse: Response
        """
        content = resp.json()
        assert resp.status_code == 200, msg or content
        assert "errors" not in list(content.keys()), msg or content

    def assertResponseHasErrors(self, resp: typing.Any, msg=None):  # type: ignore[reportMissingParameterType]
        """Assert that the call was failing.

        Take care: Even with errors, GraphQL returns status 200!
        :resp HttpResponse: Response
        """
        content = resp.json()
        assert "errors" in list(content.keys()), msg or content

    @staticmethod
    def genum(_enum: models.TextChoices | models.IntegerChoices | Enum):
        """Return appropriate enum value."""
        if _enum:
            return _enum.name
        return None

    def gdatetime(self, _datetime: datetime | None):
        if _datetime:
            return _datetime.isoformat()
        return None

    def gID(self, pk: typing.Any):
        if pk:
            return str(pk)
        return None

    def g_pagination(self, *, offset: int, limit: int, total_count: int, results: list[typing.Any]):
        return {
            "totalCount": total_count,
            "pageInfo": {"offset": offset, "limit": limit},
            "results": results,
        }

    def g_mutation_response(self, *, errors: typing.Any = None, ok: bool, result: typing.Any):
        return {
            "errors": errors,
            "ok": ok,
            "result": result,
        }

    def get_media_url(self, path: str):
        return f"http://testserver/media/{path}"

    def _dict_with_keys(
        self,
        data: dict[typing.Any, typing.Any],
        include_keys: list[str] | None = None,
        ignore_keys: list[str] | None = None,
    ):
        # TODO(thenav56): Use self.assertDictEqual instead?
        if all([ignore_keys, include_keys]):
            raise Exception("Please use one of the options among include_keys, ignore_keys")
        return {
            key: value
            for key, value in data.items()
            if ((ignore_keys is not None and key not in ignore_keys) or (include_keys is not None and key in include_keys))
        }

    def assertListDictEqual(
        self,
        left: dict[typing.Any, typing.Any],
        right: dict[typing.Any, typing.Any],
        messages: str | None = None,
        ignore_keys: list[str] | None = None,
        include_keys: list[str] | None = None,
    ):
        assert [self._dict_with_keys(item, ignore_keys=ignore_keys, include_keys=include_keys) for item in left] == [
            self._dict_with_keys(item, ignore_keys=ignore_keys, include_keys=include_keys) for item in right
        ], messages

    def no_op(*args, **_): ...

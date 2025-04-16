import dataclasses
import json
import typing

import sentry_sdk
from asgiref.sync import sync_to_async
from sentry_sdk import Scope, set_user
from sentry_sdk._types import Event, Hint
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import ignore_logger
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.strawberry import StrawberryIntegration

IGNORED_ERRORS: list[type | str] = []
IGNORED_LOGGERS = [
    "graphql.execution.utils",
    "strawberry.http.exceptions.HTTPException",
]

for _logger in IGNORED_LOGGERS:
    ignore_logger(_logger)


# TODO: Not tested
def sentry_before_send(event: Event, hint: Hint):
    # Check if the exception is a GraphQLError
    if "exception" in event and isinstance(event["exception"], dict):
        for value in event["exception"].get("values", []):
            if value.get("type") == "GraphQLError":
                # Return None to prevent sending the GraphQLError to Sentry
                return None
    return event


@dataclasses.dataclass
class SentryConfig:
    dsn: str
    release: str | None
    environment: str
    send_default_pii: bool
    traces_sample_rate: float
    profiles_sample_rate: float
    debug: bool
    # Custom configs
    monitor_celery_beat_tasks: bool
    app_type: str
    tags: dict[str, str]

    def init_sentry(self):
        integrations = [
            DjangoIntegration(),
            RedisIntegration(),
            StrawberryIntegration(async_execution=True),
            CeleryIntegration(monitor_beat_tasks=self.monitor_celery_beat_tasks),
        ]
        sentry_sdk.init(
            ignore_errors=IGNORED_ERRORS,
            integrations=integrations,
            dsn=self.dsn,
            release=self.release,
            environment=self.environment,
            send_default_pii=self.send_default_pii,
            traces_sample_rate=self.traces_sample_rate,
            profiles_sample_rate=self.profiles_sample_rate,
            before_send=sentry_before_send,
            debug=self.debug,
        )
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("app_type", self.app_type)
            for tag, value in self.tags.items():
                scope.set_tag(tag, value)


class SentryTransactionMiddlewareHelper:
    @classmethod
    @sync_to_async
    def atrack_transaction(cls, graphql_urls: set[str], request: typing.Any):
        return cls.track_transaction(graphql_urls, request)

    @staticmethod
    def track_transaction(graphql_urls: set[str], request: typing.Any):
        if request.path in graphql_urls:
            operation_type = "Query"
            operation_name = "Unknown"
            try:
                body = request.body.decode("utf-8")
                if body:
                    # XXX: This will be repeated by Strawberry as well.
                    data = json.loads(body)
                    operation_name = data.get("operationName", operation_name)
                    if data.get("query", "").startswith("mutation"):
                        operation_type = "Mutation"
            except Exception:
                ...

            scope = Scope.get_current_scope()
            scope.set_transaction_name(f"GraphQL/{operation_type}/{operation_name}")
            if (user := request.user) and user.pk:
                set_user(
                    {
                        "id": user.pk,
                        "email": user.email,
                        "is_superuser": user.is_superuser,
                    },
                )

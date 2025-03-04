from asgiref.sync import iscoroutinefunction
from django.urls import reverse
from django.utils.decorators import sync_and_async_middleware

from main.sentry import SentryTransactionMiddlewareHelper


@sync_and_async_middleware
def sentry_middleware(get_response):
    from django.conf import settings

    # One-time configuration and initialization goes here.
    graphql_urls = set([reverse("graphql")])
    if settings.DEBUG:
        graphql_urls.add(reverse("graphiql"))

    if iscoroutinefunction(get_response):

        async def amiddleware(request):
            if settings.SENTRY_ENABLED:
                await SentryTransactionMiddlewareHelper.atrack_transaction(graphql_urls, request)
            response = await get_response(request)
            return response

        return amiddleware

    def middleware(request):
        if settings.SENTRY_ENABLED:
            SentryTransactionMiddlewareHelper.track_transaction(graphql_urls, request)
        response = get_response(request)
        return response

    return middleware

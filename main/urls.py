from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt

from main.graphql.schema import CustomAsyncGraphQLView
from main.graphql.schema import schema as graphql_schema

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health-check/", include("health_check.urls")),
    path(
        "graphql/",
        CustomAsyncGraphQLView.as_view(
            schema=graphql_schema,
            graphql_ide=None,
        ),
        name="graphql",
    ),
]

if settings.DEBUG:
    urlpatterns.extend(
        [
            path(
                "graphiql/",
                csrf_exempt(  # TODO: Remove this
                    CustomAsyncGraphQLView.as_view(
                        schema=graphql_schema,
                        graphql_ide="graphiql",
                    ),
                ),
                name="graphiql",
            ),
        ]
    )

    # Static and media file URLs
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

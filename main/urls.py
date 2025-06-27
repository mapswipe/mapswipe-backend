from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from health_check.views import MainView as HealthCheckView

from apps.common.views import FirebaseAuthView, HealthCheckCustomView
from main.graphql.schema import CustomAsyncGraphQLView
from main.graphql.schema import schema as graphql_schema

base_graphql_kwargs = dict(
    schema=graphql_schema,
    multipart_uploads_enabled=True,
)


urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "graphql/",
        CustomAsyncGraphQLView.as_view(
            **base_graphql_kwargs,
            graphql_ide=None,
        ),
        name="graphql",
    ),
    # Health-check - NOTE: To include ensure_csrf_cookie decorator
    # https://github.com/revsys/django-health-check/blob/master/health_check/urls.py
    path("firebase-auth/", ensure_csrf_cookie(FirebaseAuthView.as_view()), name="firebase_auth"),
    path("health-check/", ensure_csrf_cookie(HealthCheckCustomView.as_view()), name="health_check_home"),
    path("health-check/<str:subset>/", ensure_csrf_cookie(HealthCheckView.as_view()), name="health_check_subset"),
    path("rest/docs-api", SpectacularAPIView.as_view(), name="rest-docs"),
    path("rest/docs/", SpectacularRedocView.as_view(url_name="rest-docs"), name="rest-redoc"),
    path("rest/docs-swagger/", SpectacularSwaggerView.as_view(url_name="rest-docs"), name="rest-swagger"),
]

if settings.DEBUG:
    urlpatterns.extend(
        [
            path(
                "graphiql/",
                csrf_exempt(  # TODO(thenav56): Remove this
                    CustomAsyncGraphQLView.as_view(
                        **base_graphql_kwargs,
                        graphql_ide="graphiql",
                    ),
                ),
                name="graphiql",
            ),
        ],
    )

    # Static and media file URLs
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.ENABLE_DEBUG_TOOLBAR:
    urlpatterns += debug_toolbar_urls()

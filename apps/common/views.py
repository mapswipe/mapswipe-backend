import json
import logging
import typing
from pathlib import Path

import toml
from django.conf import settings
from django.contrib.auth import login
from django.http import JsonResponse
from django.utils.translation import gettext
from drf_spectacular.utils import extend_schema
from health_check.views import MainView  # type: ignore[reportMissingTypeStubs]
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.contributor.models import ContributorUser

from .serializers import FirebaseAuthRequestSerializer

logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from rest_framework.request import Request

    from utils.git import GitHelper

    from .types import FirebaseDecodedIdToken


# FIXME: Maybe a better approach then this?
def _get_version_from_pyproject(base_path: Path) -> str:
    data = toml.load(settings.BASE_DIR / base_path / "pyproject.toml")
    return data["project"]["version"]


class HealthCheckCustomView(MainView):
    @typing.override
    def render_to_response_json(
        self,
        plugins: typing.Any,
        status: typing.Any,
    ):
        response = super().render_to_response_json(plugins, status)
        git_helper: GitHelper = settings.GIT_HELPER
        data = {
            **json.loads(response.content),
            "app": {
                "environment": settings.APP_ENVIRONMENT,
                "version": _get_version_from_pyproject(settings.BASE_DIR),
                "git": {
                    "branch": git_helper.branch,
                    "commit": git_helper.commit_sha,
                    "repository": {
                        "url": git_helper.repository_url,
                        "branch": git_helper.branch_url,
                        "commit": git_helper.commit_url,
                        "commit_github_metadata": git_helper.commit_github_metadata,
                    },
                },
            },
        }
        return JsonResponse(
            data,
            status=response.status_code,
        )


# https://firebase.google.com/docs/auth/admin/verify-id-tokens
class FirebaseAuthView(APIView):
    authentication_classes = []
    permission_classes = []

    @staticmethod
    def _400_response(message: str) -> Response:
        return Response({"non_field_errors": [message]}, 400)

    @extend_schema(
        description=gettext("use firebase id_token to authenticate"),
        request=FirebaseAuthRequestSerializer,
        responses=None,
    )
    def post(self, request: "Request"):
        token_serializer = FirebaseAuthRequestSerializer(data=request.data)
        if not token_serializer.is_valid():
            return Response(token_serializer.errors, 400)
        token: FirebaseDecodedIdToken = token_serializer.validated_data["token"]
        user = token_serializer.validated_data["user"]

        if user.contributor_user is not None:
            if user.contributor_user.firebase_id != token.uid:
                return self._400_response(
                    gettext(
                        "Provided firebase_id didn't match with the existing user's email configuration."
                        " If you think this is a unexpected, please contact system admin to resolve this issue.",
                    ),
                )
        else:
            contributor_user = ContributorUser.objects.filter(firebase_id=token.uid).first()
            if contributor_user is None:
                return self._400_response(
                    gettext(
                        "Provided firebase_id doesn't exists in this system."
                        " If you think this is a unexpected, please contact system admin to resolve this issue.",
                    ),
                )

            user.contributor_user = contributor_user
            user.save(update_fields=("contributor_user",))

        login(request, user)

        return Response(status=200)

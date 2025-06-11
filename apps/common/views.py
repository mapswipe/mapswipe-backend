import json
import typing
from pathlib import Path

import toml
from django.conf import settings
from django.http import JsonResponse
from health_check.views import MainView

if typing.TYPE_CHECKING:
    from utils.git import GitHelper


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

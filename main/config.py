import os
import typing

from django.conf import settings

if typing.TYPE_CHECKING:
    from pathlib import Path
    from urllib.parse import ParseResult as URLParseResult

    from utils.firebase import FirebaseHelper


class Config:
    BASE_DIR = typing.cast("Path", settings.BASE_DIR)

    # NOTE: We get AOI for validate from HOT tasking manager
    HOT_TASKING_MANAGER_PROJECT_API_LINK = "https://tasking-manager-production-api.hotosm.org/api/v2/"

    # NOTE: We get build footprints for validate from OHSOME
    OHSOME_API_LINK = "https://api.ohsome.org/v1/"
    # NOTE: We get changeset information from OSMCha
    OSMCHA_API_LINK = "https://osmcha.org/api/v1/"
    OSMCHA_API_KEY = typing.cast("str", settings.OSMCHA_API_KEY)
    # NOTE: We get changeset information if missing from OSMCha
    OSM_API_LINK = "https://www.openstreetmap.org/api/0.6/"

    FIREBASE_HELPER = typing.cast("FirebaseHelper", settings.FIREBASE_HELPER)
    FIREBASE_EMULATOR_USE = typing.cast("str | None", settings.FIREBASE_EMULATOR_USE)
    FIREBASE_EMULATOR_TEST_HOST = typing.cast("str | None", settings.FIREBASE_EMULATOR_TEST_HOST)
    FIREBASE_EMULATOR_HOST = os.environ.get("FIREBASE_DATABASE_EMULATOR_HOST")

    ENABLE_DANGER_MODE = typing.cast("bool", settings.ENABLE_DANGER_MODE)

    # Existing database
    EXISTING_SYSTEM_CONNECT_ENABLED = typing.cast("bool", settings.EXISTING_SYSTEM_CONNECT_ENABLED)
    EXISTING_SYSTEM_POSTGRES_KEY = typing.cast("str", settings.EXISTING_SYSTEM_POSTGRES_KEY)
    EXISTING_SYSTEM_API = typing.cast("URLParseResult", getattr(settings, "EXISTING_SYSTEM_API", None))
    EXISTING_SYSTEM_API_INSECURE = typing.cast("bool", getattr(settings, "EXISTING_SYSTEM_API_INSECURE", False))

    class FirebaseKeys:
        @staticmethod
        def backend_wait():
            return "/backendWait"

        @staticmethod
        def v2():
            return "/v2"

        @staticmethod
        def project(project_id: str):
            return f"/v2/projects/{project_id}"

        @staticmethod
        def project_groups(project_id: str):
            return f"/v2/groups/{project_id}/"

        @staticmethod
        def project_tasks(project_id: str):
            return f"/v2/tasks/{project_id}/"

        @staticmethod
        def tutorial(tutorial_id: str):
            return f"/v2/projects/{tutorial_id}"

        @staticmethod
        def tutorial_groups(tutorial_id: str):
            return f"/v2/groups/{tutorial_id}/"

        @staticmethod
        def tutorial_tasks(tutorial_id: str):
            return f"/v2/tasks/{tutorial_id}/"

        @staticmethod
        def organization(organization_id: str):
            return f"/v2/organisations/{organization_id}/"

        @staticmethod
        def contributor_team(contributor_team_id: str):
            return f"/v2/teams/{contributor_team_id}/"

        @staticmethod
        def contributor_user(user_id: str):
            return f"/v2/users/{user_id}"

        @staticmethod
        def contributor_user_group(group_id: str | int):  # TODO: int?
            return f"/v2/userGroups/{group_id}"

        @staticmethod
        def results_projects():
            return "/v2/results/"

        @staticmethod
        def results_project_groups(project_id: str):
            return f"/v2/results/{project_id}"


# FIXME: Import utils/geo/raster_tile_server/config.py here
# FIXME: Import utils/geo/vector_tile_server/config.py here

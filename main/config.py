import os
import typing

from django.conf import settings

if typing.TYPE_CHECKING:
    from utils.firebase import FirebaseHelper


class Config:
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

    # Existing database
    EXISTING_POSTGRES_ENABLED = typing.cast("bool", settings.EXISTING_POSTGRES_ENABLED)
    EXISTING_DATABASE_KEY = typing.cast("str", settings.EXISTING_DATABASE_KEY)

    class FirebaseKeys:
        @staticmethod
        def backend_wait():
            return "/backendWait"

        @staticmethod
        def v2():
            return "/v2"

        @staticmethod
        def project(project_id: str | int):
            return f"/v2/projects/{project_id}"

        @staticmethod
        def project_groups(project_id: str | int):
            return f"/v2/groups/{project_id}/"

        @staticmethod
        def project_tasks(project_id: str | int):
            return f"/v2/tasks/{project_id}/"

        @staticmethod
        def organization(organization_id: str | int):
            return f"/v2/organisation/{organization_id}/"

        @staticmethod
        def contributor_team(contributor_team_id: str | int):
            return f"/v2/teams/{contributor_team_id}/"

        @staticmethod
        def contributor_user(user_id: str | int):
            return f"/v2/users/{user_id}"


# FIXME: Import utils/geo/raster_tile_server/config.py here
# FIXME: Import utils/geo/vector_tile_server/config.py here

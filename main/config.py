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


# FIXME: Import utils/geo/raster_tile_server/config.py here
# FIXME: Import utils/geo/vector_tile_server/config.py here

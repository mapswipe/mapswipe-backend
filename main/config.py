import typing

from django.conf import settings


class Config:
    OHSOME_API_LINK = "https://api.ohsome.org/v1/"
    OSMCHA_API_LINK = "https://osmcha.org/api/v1/"
    # FIXME(tnagorra): Make this configurable
    OSM_API_LINK = "https://www.openstreetmap.org/api/0.6/"
    OSMCHA_API_KEY = typing.cast("str", settings.OSMCHA_API_KEY)


# FIXME: Import utils/geotile_server/config.py here

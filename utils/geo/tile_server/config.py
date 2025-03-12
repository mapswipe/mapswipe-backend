from django.conf import settings
from django.db import models


class TileServerName(models.IntegerChoices):
    CUSTOM = 1, "Custom"
    BING = 2, "Bing"
    MAPBOX = 3, "Mapbox"
    MAXAR_STANDARD = 4, "Maxar Standard"
    MAXAR_PREMIUM = 5, "Maxar Premium"
    ESRI = 6, "ESRI World Imagery"
    ESRI_BETA = 7, "ESRI World Imagery (Clarity) Beta"
    # TODO: Confirm if we have more/less


class Config:
    IMAGE_URLS = {
        TileServerName.BING: ("https://ecn.t0.tiles.virtualearth.net" + "/tiles/a{quad_key}.jpeg?g=7505&token={key}"),
        TileServerName.MAPBOX: ("https://d.tiles.mapbox.com" + "/v4/mapbox.satellite/{z}/{x}/{y}.jpg?access_token={key}"),
        TileServerName.MAXAR_PREMIUM: (
            "https://services.digitalglobe.com"
            + "/earthservice/tmsaccess/tms/1.0.0/"
            + "DigitalGlobe%3AImageryTileService@EPSG%3A3857@jpg/"
            + "{z}/{x}/{y}.jpg?connectId={key}"
        ),
        TileServerName.MAXAR_STANDARD: (
            "https://services.digitalglobe.com"
            + "/earthservice/tmsaccess/tms/1.0.0/"
            + "DigitalGlobe%3AImageryTileService@EPSG%3A3857@jpg/"
            + "{z}/{x}/{y}.jpg?connectId={key}"
        ),
        TileServerName.ESRI: (
            "https://services.arcgisonline.com" + "/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        TileServerName.ESRI_BETA: (
            "https://clarity.maptiles.arcgis.com" + "/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        # "sinergise": (
        #     "https://services.sentinel-hub.com"
        #     + "/ogc/wmts/{key}?request=getTile&tilematrixset=PopularWebMercator256&"
        #     + "tilematrix={z}&tilecol={x}&tilerow={y}&layer={layer}"
        # ),
    }

    IMAGE_API_KEYS = {
        TileServerName.BING: settings.MAP_IMAGE_BING_API_KEY,
        TileServerName.MAPBOX: settings.MAP_IMAGE_MAPBOX_API_KEY,
        TileServerName.MAXAR_STANDARD: settings.MAP_IMAGE_MAXAR_STANDARD_API_KEY,
        TileServerName.MAXAR_PREMIUM: settings.MAP_IMAGE_MAXAR_PREMIUM_API_KEY,
        TileServerName.ESRI: settings.MAP_IMAGE_ESRI_API_KEY,
        TileServerName.ESRI_BETA: settings.MAP_IMAGE_ESRI_BETA_API_KEY,
        # "digital_globe": settings.MAP_IMAGE_DIGITAL_GLOBE_API_KEY,
    }

from django.conf import settings
from django.db import models


class TileServerNameEnum(models.TextChoices):
    CUSTOM = "CUSTOM", "Custom"
    BING = "BING", "Bing"
    MAPBOX = "MAPBOX", "Mapbox"
    MAXAR_STANDARD = "MAXAR_STANDARD", "Maxar Standard"
    MAXAR_PREMIUM = "MAXAR_PREMIUM", "Maxar Premium"
    ESRI = "ESRI", "ESRI World Imagery"
    ESRI_BETA = "ESRI_BETA", "ESRI World Imagery (Clarity) Beta"
    # TODO: Confirm if we have more/less


class Config:
    IMAGE_URLS = {
        TileServerNameEnum.BING: ("https://ecn.t0.tiles.virtualearth.net" + "/tiles/a{quad_key}.jpeg?g=7505&token={key}"),
        TileServerNameEnum.MAPBOX: (
            "https://d.tiles.mapbox.com" + "/v4/mapbox.satellite/{z}/{x}/{y}.jpg?access_token={key}"
        ),
        TileServerNameEnum.MAXAR_PREMIUM: (
            "https://services.digitalglobe.com"
            "/earthservice/tmsaccess/tms/1.0.0/"
            "DigitalGlobe%3AImageryTileService@EPSG%3A3857@jpg/"
            "{z}/{x}/{y}.jpg?connectId={key}"
        ),
        TileServerNameEnum.MAXAR_STANDARD: (
            "https://services.digitalglobe.com"
            "/earthservice/tmsaccess/tms/1.0.0/"
            "DigitalGlobe%3AImageryTileService@EPSG%3A3857@jpg/"
            "{z}/{x}/{y}.jpg?connectId={key}"
        ),
        TileServerNameEnum.ESRI: (
            "https://services.arcgisonline.com" + "/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        TileServerNameEnum.ESRI_BETA: (
            "https://clarity.maptiles.arcgis.com" + "/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        # "sinergise": (
        #     "https://services.sentinel-hub.com"
        #     + "/ogc/wmts/{key}?request=getTile&tilematrixset=PopularWebMercator256&"
        #     + "tilematrix={z}&tilecol={x}&tilerow={y}&layer={layer}"
        # ),
    }

    IMAGE_API_KEYS = {
        TileServerNameEnum.BING: settings.MAP_IMAGE_BING_API_KEY,
        TileServerNameEnum.MAPBOX: settings.MAP_IMAGE_MAPBOX_API_KEY,
        TileServerNameEnum.MAXAR_STANDARD: settings.MAP_IMAGE_MAXAR_STANDARD_API_KEY,
        TileServerNameEnum.MAXAR_PREMIUM: settings.MAP_IMAGE_MAXAR_PREMIUM_API_KEY,
        TileServerNameEnum.ESRI: settings.MAP_IMAGE_ESRI_API_KEY,
        TileServerNameEnum.ESRI_BETA: settings.MAP_IMAGE_ESRI_BETA_API_KEY,
        # "digital_globe": settings.MAP_IMAGE_DIGITAL_GLOBE_API_KEY,
    }

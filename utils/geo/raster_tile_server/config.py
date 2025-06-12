from django.conf import settings
from django.db import models


class RasterTileServerNameEnum(models.TextChoices):
    CUSTOM = "CUSTOM", "Custom"
    BING = "BING", "Bing"
    MAPBOX = "MAPBOX", "Mapbox"
    MAXAR_STANDARD = "MAXAR_STANDARD", "Maxar Standard"
    MAXAR_PREMIUM = "MAXAR_PREMIUM", "Maxar Premium"
    ESRI = "ESRI", "ESRI World Imagery"
    ESRI_BETA = "ESRI_BETA", "ESRI World Imagery (Clarity) Beta"
    # TODO(thenav56): Confirm if we have more/less


class Config:
    # FIXME(tnagorra): This will be obsolete soon
    IMAGE_URLS = {
        RasterTileServerNameEnum.BING: ("https://ecn.t0.tiles.virtualearth.net/tiles/a{quadkey}.jpeg?g=7505&token={key}"),
        RasterTileServerNameEnum.MAPBOX: (
            "https://d.tiles.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}.jpg?access_token={key}"
        ),
        RasterTileServerNameEnum.MAXAR_PREMIUM: (
            "https://services.digitalglobe.com"
            "/earthservice/tmsaccess/tms/1.0.0/"
            "DigitalGlobe%3AImageryTileService@EPSG%3A3857@jpg/"
            "{z}/{x}/{y}.jpg?connectId={key}"
        ),
        RasterTileServerNameEnum.MAXAR_STANDARD: (
            "https://services.digitalglobe.com"
            "/earthservice/tmsaccess/tms/1.0.0/"
            "DigitalGlobe%3AImageryTileService@EPSG%3A3857@jpg/"
            "{z}/{x}/{y}.jpg?connectId={key}"
        ),
        RasterTileServerNameEnum.ESRI: (
            "https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        RasterTileServerNameEnum.ESRI_BETA: (
            "https://clarity.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        # "sinergise": (
        #     "https://services.sentinel-hub.com"
        #     + "/ogc/wmts/{key}?request=getTile&tilematrixset=PopularWebMercator256&"
        #     + "tilematrix={z}&tilecol={x}&tilerow={y}&layer={layer}"
        # ),
    }

    # FIXME(tnagorra): This will be obsolete soon
    IMAGE_API_KEYS = {
        RasterTileServerNameEnum.BING: settings.MAP_IMAGE_BING_API_KEY,
        RasterTileServerNameEnum.MAPBOX: settings.MAP_IMAGE_MAPBOX_API_KEY,
        RasterTileServerNameEnum.MAXAR_STANDARD: settings.MAP_IMAGE_MAXAR_STANDARD_API_KEY,
        RasterTileServerNameEnum.MAXAR_PREMIUM: settings.MAP_IMAGE_MAXAR_PREMIUM_API_KEY,
        RasterTileServerNameEnum.ESRI: settings.MAP_IMAGE_ESRI_API_KEY,
        RasterTileServerNameEnum.ESRI_BETA: settings.MAP_IMAGE_ESRI_BETA_API_KEY,
        # "digital_globe": settings.MAP_IMAGE_DIGITAL_GLOBE_API_KEY,
    }

    IMAGE_URLS_WITH_KEY = {
        RasterTileServerNameEnum.BING: (
            f"https://ecn.t0.tiles.virtualearth.net/tiles/a{{quadkey}}.jpeg?g=7505&token={settings.MAP_IMAGE_BING_API_KEY}"
        ),
        RasterTileServerNameEnum.MAPBOX: (
            "https://d.tiles.mapbox.com"
            "/v4/mapbox.satellite"
            "/{z}/{x}/{y}.jpg"
            f"?access_token={settings.MAP_IMAGE_MAPBOX_API_KEY}"
        ),
        RasterTileServerNameEnum.MAXAR_PREMIUM: (
            "https://services.digitalglobe.com"
            "/earthservice/tmsaccess/tms/1.0.0/DigitalGlobe%3AImageryTileService@EPSG%3A3857@jpg"
            "/{z}/{x}/{y}.jpg"
            f"?connectId={settings.MAP_IMAGE_MAXAR_PREMIUM_API_KEY}"
        ),
        RasterTileServerNameEnum.MAXAR_STANDARD: (
            "https://services.digitalglobe.com"
            "/earthservice/tmsaccess/tms/1.0.0/DigitalGlobe%3AImageryTileService@EPSG%3A3857@jpg"
            "/{z}/{x}/{y}.jpg"
            f"?connectId={settings.MAP_IMAGE_MAXAR_STANDARD_API_KEY}"
        ),
        RasterTileServerNameEnum.ESRI: (
            "https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        RasterTileServerNameEnum.ESRI_BETA: (
            "https://clarity.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        # "sinergise": (
        #     "https://services.sentinel-hub.com"
        #     f"/ogc/wmts/{settings.MAP_IMAGE_SINERGISE_API_KEY}?request=getTile&tilematrixset=PopularWebMercator256&"
        #     "tilematrix={z}&tilecol={x}&tilerow={y}&layer={layer}"
        # ),
    }

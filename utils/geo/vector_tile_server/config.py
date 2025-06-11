from django.db import models


class VectorTileServerNameEnum(models.TextChoices):
    CUSTOM = "CUSTOM", "Custom"
    OPEN_STREET_MAP = "OPEN_STREET_MAP", "Open Street Map"
    OPEN_FREE_MAP = "OPEN_FREE_MAP", "Open Free Map"
    VERSATILES = "VERSATILES", "Versatiles"


class VectorConfig:
    VECTOR_IMAGE_URLS = {
        # Style JSON: "https://vector.osm.org/demo/shortbread/colorful.json",
        VectorTileServerNameEnum.OPEN_STREET_MAP: "https://vector.osm.org/shortbread_v1/{z}/{x}/{y}.mvt",
        # Style JSON: "https://tiles.openfreemap.org/styles/liberty",
        VectorTileServerNameEnum.OPEN_FREE_MAP: "https://tiles.openfreemap.org/planet/20250528_001001_pt/{z}/{x}/{y}.pbf",
        # Style JSON: "https://tiles.versatiles.org/assets/styles/colorful/style.json",
        VectorTileServerNameEnum.VERSATILES: "https://tiles.versatiles.org/tiles/osm/{z}/{x}/{y}",
    }

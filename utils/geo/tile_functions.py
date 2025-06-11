"""
Copied from https://github.com/mapswipe/python-mapswipe-workers/blob/bf576a0/mapswipe_workers/mapswipe_workers/utils/tile_functions.py
"""

import math

from osgeo import ogr


class _Point:
    """
    The basic class point representing a Pixel
    Attributes
    ----------
    x : int
        x coordinate
    y : int
        y coordinate
    """

    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y


class _Tile:
    """
    The basic class tile representing a TMS tile

    Attributes
    ----------
    x : int
        x coordinate
    y : int
        y coordinate
    """

    def __init__(self, x: int = 0, y: int = 0):
        self.x = x
        self.y = y


def lat_long_zoom_to_pixel_coords(lat: float, lon: float, zoom: int):
    """Compute pixel coordinates from lat-long point at a given zoom level."""

    p = _Point()
    sinLat = math.sin(lat * math.pi / 180.0)
    x = ((lon + 180) / 360) * 256 * math.pow(2, zoom)
    y = (
        (0.5 - math.log((1 + sinLat) / (1 - sinLat)) / (4 * math.pi))
        * 256  # noqa: W503
        * math.pow(2, zoom)  # noqa: W503
    )
    p.x = int(math.floor(x))
    p.y = int(math.floor(y))
    return p


def pixel_coords_zoom_to_lat_lon(pile_x: float, pile_y: float, zoom: int):
    """Compute latitude, longitude from pixel coordinates at a given zoom level."""

    MapSize = 256 * math.pow(2, zoom)
    x = (pile_x / MapSize) - 0.5
    y = 0.5 - (pile_y / MapSize)
    lon = 360 * x
    lat = 90 - 360 * math.atan(math.exp(-y * 2 * math.pi)) / math.pi

    return lon, lat


def pixel_coords_to_tile_address(pixel_x: float, pixel_y: float):
    """Compute a tile address from pixel coordinates of point within tile."""

    t = _Tile()
    t.x = int(math.floor(pixel_x / 256))
    t.y = int(math.floor(pixel_y / 256))
    return t


def tile_coords_and_zoom_to_quadKey(tile_x: int, tile_y: int, zoom: int) -> str:
    """Create a quadkey for use with certain tileservers that use them, e.g. Bing."""

    quadKey = ""
    for i in range(zoom, 0, -1):
        digit = 0
        mask = 1 << (i - 1)
        if (tile_x & mask) != 0:
            digit += 1
        if (tile_y & mask) != 0:
            digit += 2
        quadKey += str(digit)
    return quadKey


# FIXME(tnagorra): This is not used.
def quadkey_to_bing_url(quadkey: str, api_key: str):
    """Create a tile image URL linking to a Bing tile server."""
    # FIXME(tnagorra): We should not hardcode the urls
    return f"https://ecn.t0.tiles.virtualearth.net/tiles/a{quadkey}.jpeg?g=7505&mkt=en-US&token={api_key}"


# FIXME(tnagorra): Add typings for osgeo
def geometry_from_tile_coords(tile_x: float, tile_y: float, zoom: int) -> str:
    """Compute the polygon geometry of a tile map service tile."""

    # Calculate lat, lon of upper left corner of tile
    pixel_x = tile_x * 256
    pixel_y = tile_y * 256
    lon_left, lat_top = pixel_coords_zoom_to_lat_lon(pixel_x, pixel_y, zoom)

    # Calculate lat, lon of lower right corner of tile
    pixel_x = (tile_x + 1) * 256
    pixel_y = (tile_y + 1) * 256
    lon_right, lat_bottom = pixel_coords_zoom_to_lat_lon(pixel_x, pixel_y, zoom)

    # Create Geometry
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(lon_left, lat_top)
    ring.AddPoint(lon_right, lat_top)
    ring.AddPoint(lon_right, lat_bottom)
    ring.AddPoint(lon_left, lat_bottom)
    ring.AddPoint(lon_left, lat_top)
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)

    if poly.GetCoordinateDimension() == 3:
        poly.FlattenTo2D()

    return poly.ExportToWkt()

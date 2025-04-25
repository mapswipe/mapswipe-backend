"""
Copied from https://github.com/mapswipe/python-mapswipe-workers/blob/bf576a0/mapswipe_workers/mapswipe_workers/utils/tile_grouping_functions.py
"""

import logging
import math
import typing

from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GeometryCollection, LinearRing, Polygon

from . import tile_functions

logger = logging.getLogger(__name__)

# NOTE: x_min, y_min, x_max, y_max
type GeoExtent = tuple[float, float, float, float]


class HorizontalSliceInfo(typing.TypedDict):
    tile_y_top: list[int]
    tile_y_bottom: list[int]
    slice_collection: GeometryCollection


class RawGroup(typing.TypedDict):
    xMin: int
    xMax: int
    yMin: int
    yMax: int
    # FIXME(tnagorra): This seems to be unused. This might still be used in exports
    group_polygon: Polygon


# FIXME(tnagorra): This seems to be unused
class UnSupportedGeoExtensionException(Exception):
    pass


class AoiGeometry(typing.TypedDict):
    extent: GeoExtent
    polygons: list[Polygon]


def get_geometry_from_file(infile: str) -> AoiGeometry:
    data_source = DataSource(infile)

    # Get the data layer
    # TODO(thenav56): Proper validation
    assert data_source.layer_count == 1
    layer = data_source[0]

    # get feature geometry of all features of the input file
    polygons = []
    for feature in layer:
        polygons.append(feature.geom.geos)

    return {
        "extent": layer.extent.tuple,
        "polygons": polygons,
    }


def _get_horizontal_slice(
    extent: GeoExtent,
    polygons: list[Polygon],
    zoom: int,
) -> HorizontalSliceInfo:
    """
    The function slices all input geometries vertically
    using a height of max 3 tiles per geometry.
    The function iterates over all input geometries.
    For each geometry tile coordinates are calculated.
    Then this geometry is split into several geometries using the min
    and max tile coordinates for the geometry.
    """

    tile_y_top: list[int] = []
    tile_y_bottom: list[int] = []
    slice_collection = GeometryCollection()

    xmin = extent[0]
    ymin = extent[1]
    xmax = extent[2]
    ymax = extent[3]

    for polygon_to_slice in polygons:
        # get upper left left tile coordinates
        pixel = tile_functions.lat_long_zoom_to_pixel_coords(ymax, xmin, zoom)
        tile = tile_functions.pixel_coords_to_tile_address(pixel.x, pixel.y)
        TileX_left = tile.x
        TileY_top = tile.y

        # get lower right tile coordinates
        pixel = tile_functions.lat_long_zoom_to_pixel_coords(ymin, xmax, zoom)
        tile = tile_functions.pixel_coords_to_tile_address(pixel.x, pixel.y)

        TileX_right = tile.x
        TileY_bottom = tile.y
        TileHeight = abs(TileY_top - TileY_bottom)

        TileY = TileY_top

        # get rows
        rows = int(math.ceil(TileHeight / 3))

        ############################################################

        for _ in range(0, rows + 1):
            # Calculate lat, lon of upper left corner of tile
            PixelX = TileX_left * 256
            PixelY = TileY * 256
            lon_left, lat_top = tile_functions.pixel_coords_zoom_to_lat_lon(PixelX, PixelY, zoom)

            PixelX = TileX_right * 256
            PixelY = (TileY + 3) * 256
            lon_right, lat_bottom = tile_functions.pixel_coords_zoom_to_lat_lon(PixelX, PixelY, zoom)

            # Create Geometry
            poly = Polygon(
                LinearRing(
                    (lon_left, lat_top),
                    (lon_right, lat_top),
                    (lon_right, lat_bottom),
                    (lon_left, lat_bottom),
                    (lon_left, lat_top),
                ),
            )

            sliced_poly = poly.intersection(polygon_to_slice)

            if sliced_poly:
                if sliced_poly.geom_type.upper() == "POLYGON":
                    tile_y_top.append(TileY)
                    tile_y_bottom.append(TileY + 3)
                    slice_collection.append(sliced_poly)
                elif sliced_poly.geom_type.upper() == "MULTIPOLYGON":
                    for geom_part in sliced_poly:
                        tile_y_top.append(TileY)
                        tile_y_bottom.append(TileY + 3)
                        slice_collection.append(geom_part)

            TileY = TileY + 3

    return HorizontalSliceInfo(
        tile_y_top=tile_y_top,
        tile_y_bottom=tile_y_bottom,
        slice_collection=slice_collection,
    )


def _get_vertical_slice(
    slice_infos: HorizontalSliceInfo,
    zoom: int,
    width_threshold: int = 40,
) -> dict[str, RawGroup]:
    """
    The function slices the horizontal stripes vertically.
    Each input stripe has a height of three tiles
    and will be split into vertical parts.
    The width of each part is defined by the width threshold set below.

    Parameters
    ----------
    slice_infos: HorizontalSliceInfo
    zoom: int
        the tile map service zoom level
    width_threshold:  int
        the number of vertical tiles for a group,
        this defines how "long" groups are.

    Returns
    -------
    raw_groups : dict
        a dictionary containing "xMin", "xMax", "yMin", "yMax"
        and a "group_polygon" as ogr.Geometry(ogr.wkbPolygon)
        and the "group_id" as key
    """

    # create an empty dict for the group ids
    # and TileY_min, TileY_may, TileX_min, TileX_max
    raw_groups: dict[str, RawGroup] = {}
    group_id = 100

    # add these variables to test, if groups are created correctly
    TileY_top = -1

    geom_collections: GeometryCollection = slice_infos["slice_collection"]

    # process each polygon individually
    for p, horizontal_slice in enumerate(geom_collections):
        # sometimes we get really really small polygons, skip these
        if horizontal_slice.area < 0.0000001:
            continue

        extent = horizontal_slice.extent
        xmin = extent[0]
        ymin = extent[1]
        xmax = extent[2]
        ymax = extent[3]

        # get upper left left tile coordinates
        pixel = tile_functions.lat_long_zoom_to_pixel_coords(ymax, xmin, zoom)
        tile = tile_functions.pixel_coords_to_tile_address(pixel.x, pixel.y)
        TileX_left = tile.x

        # get lower right tile coordinates
        pixel = tile_functions.lat_long_zoom_to_pixel_coords(ymin, xmax, zoom)
        tile = tile_functions.pixel_coords_to_tile_address(pixel.x, pixel.y)
        TileX_right = tile.x

        # we don't compute tile y top and tile y bottom coordinates again,
        # but get the ones from the list
        # doing so we can avoid problems due to rounding errors
        # which result in wrong tile coordinates
        TileY_top = slice_infos["tile_y_top"][p]
        TileY_bottom = slice_infos["tile_y_bottom"][p]

        TileWidth = abs(TileX_right - TileX_left)
        TileX = TileX_left

        # get columns
        cols = int(math.ceil(TileWidth / width_threshold))
        # avoid zero division error and check if cols is smaller than zero
        if cols < 1:
            continue

        # how wide should the group be, calculate from total width
        # and do equally for all slices
        step_size = math.ceil(TileWidth / cols)

        # the step_size should be always and even number
        # this will make sure that there will be always 6 tasks per screen
        if step_size % 2 == 1:
            step_size += 1

        for i in range(0, cols):
            # we need to make sure that geometries are not clipped at the edge
            if i == (cols - 1):
                step_size = TileX_right - TileX + 1
                if step_size % 2 == 1:
                    step_size += 1

            # Calculate lat, lon of upper left corner of tile
            PixelX = TileX * 256
            PixelY = TileY_top * 256
            lon_left, lat_top = tile_functions.pixel_coords_zoom_to_lat_lon(PixelX, PixelY, zoom)
            # logging.info('lon_left: %s, lat_top: %s' % (lon_left, lat_top))

            PixelX = (TileX + step_size) * 256
            PixelY = TileY_bottom * 256
            lon_right, lat_bottom = tile_functions.pixel_coords_zoom_to_lat_lon(PixelX, PixelY, zoom)

            # TODO(thenav56): line 254-262 does exactly the same as in line 345-352,
            # maybe put it in a function create_geom_from_group_coords
            # Create Geometry

            group_poly = Polygon(
                LinearRing(
                    (lon_left, lat_top),
                    (lon_right, lat_top),
                    (lon_right, lat_bottom),
                    (lon_left, lat_bottom),
                    (lon_left, lat_top),
                ),
            )

            # add info to groups_dict
            group_id += 1
            group_id_string = f"g{group_id}"
            raw_groups[group_id_string] = {
                "xMin": TileX,
                "xMax": TileX + step_size - 1,
                "yMin": TileY_top,
                "yMax": TileY_bottom - 1,
                "group_polygon": group_poly,  # XXX: Not used
            }

            TileX = TileX + step_size

    logger.info("created vertical_slice")
    return raw_groups


def _groups_intersect(group_a: RawGroup, group_b: RawGroup) -> bool:
    """Check if groups intersect."""
    x_max = int(group_a["xMax"])
    x_min = int(group_a["xMin"])
    y_max = int(group_a["yMax"])
    y_min = int(group_a["yMin"])

    x_maxB = int(group_b["xMax"])
    x_minB = int(group_b["xMin"])
    y_maxB = int(group_b["yMax"])
    y_minB = int(group_b["yMin"])

    return (x_min <= x_maxB) and (x_minB <= x_max) and (y_min <= y_maxB) and (y_minB <= y_max)


def _merge_groups(group_a: RawGroup, group_b: RawGroup, zoom: int) -> RawGroup:
    """Merge two overlapping groups into a single group.

    This can result in groups that are "longer" than
    the groups set in the first place and they can be
    longer than the initial groupSize defined by the project
    manager.
    """

    x_max = int(group_a["xMax"])
    x_min = int(group_a["xMin"])
    y_max = int(group_a["yMax"])
    y_min = int(group_a["yMin"])

    x_maxB = int(group_b["xMax"])
    x_minB = int(group_b["xMin"])

    # if two groups overlap, merge into one group
    new_x_min = min([x_min, x_minB])
    new_x_max = max([x_max, x_maxB])

    # check if group_x_size is even and adjust new_x_max
    if (new_x_max - new_x_min + 1) % 2 == 1:
        new_x_max += 1

    # Calculate lat, lon of upper left corner of tile
    PixelX = int(new_x_min) * 256
    PixelY = (int(y_max) + 1) * 256
    lon_left, lat_top = tile_functions.pixel_coords_zoom_to_lat_lon(PixelX, PixelY, zoom)
    # logging.info('lon_left: %s, lat_top: %s' % (lon_left, lat_top))

    # Calculate lat, lon of bottom right corner of tile
    PixelX = (int(new_x_max) + 1) * 256
    PixelY = int(y_min) * 256
    lon_right, lat_bottom = tile_functions.pixel_coords_zoom_to_lat_lon(PixelX, PixelY, zoom)

    # Create Geometry
    poly = Polygon(
        LinearRing(
            (lon_left, lat_top),
            (lon_right, lat_top),
            (lon_right, lat_bottom),
            (lon_left, lat_bottom),
            (lon_left, lat_top),
        ),
    )

    new_group: RawGroup = {
        "xMin": new_x_min,
        "xMax": new_x_max,
        "yMin": y_min,
        "yMax": y_max,
        "group_polygon": poly,  # XXX: Not used
    }

    return new_group


def _adjust_overlapping_groups(
    groups: dict[str, RawGroup],
    zoom: int,
) -> tuple[dict[str, RawGroup], int]:
    """Loop through groups dict and merge overlapping groups."""

    groups_without_overlap: dict[str, RawGroup] = {}
    overlaps_total = 0

    for group_id in list(groups.keys()):
        # skip if groups has been removed already
        if group_id not in groups:
            continue

        overlap_count = 0
        for group_id_b in list(groups.keys()):
            # skip if it is the same group
            if group_id_b == group_id:
                continue

            if _groups_intersect(groups[group_id], groups[group_id_b]):
                overlap_count += 1
                new_group = _merge_groups(groups[group_id], groups[group_id_b], zoom)
                del groups[group_id_b]
                groups_without_overlap[group_id] = new_group

        if overlap_count == 0:
            groups_without_overlap[group_id] = groups[group_id]

        del groups[group_id]
        overlaps_total += overlap_count

    logger.info("overlaps_total: %s", overlaps_total)
    return groups_without_overlap, overlaps_total


def extent_to_groups(aoi_geometry: AoiGeometry, zoom: int, groupSize: int) -> dict[str, RawGroup]:
    """
    The function to polygon geometries of a given input file
    into horizontal slices and then vertical slices.

    Parameters
    ----------
    infile : str
        the path to the .shp, .kml
        or .geojson file containing the input geometries
    zoom : int
        the tile map service zoom level

    Returns
    -------
    raw_groups_dict : dict
        a dictionary containing "xMin", "xMax", "yMin", "yMax"
        and a "group_polygon" as ogr.Geometry(ogr.wkbPolygon)
        and the "group_id" as key
    """
    extent = aoi_geometry["extent"]
    polygons = aoi_geometry["polygons"]

    # get horizontal slices --> rows
    horizontal_slice_infos = _get_horizontal_slice(extent, polygons, zoom)

    # then get vertical slices --> columns
    raw_groups_dict = _get_vertical_slice(horizontal_slice_infos, zoom, groupSize)

    # finally remove overlapping groups
    groups_dict, overlaps_total = _adjust_overlapping_groups(raw_groups_dict, zoom)

    # check if there are still overlaps
    c = 0
    while overlaps_total > 0:
        c += 1
        # avoid that this runs forever
        if c == 5:
            break

        groups_dict, overlaps_total = _adjust_overlapping_groups(groups_dict.copy(), zoom)

    return groups_dict

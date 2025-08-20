import json
import logging
import typing
from pathlib import Path

from osgeo import ogr, osr

logger = logging.getLogger(__name__)


class ProjectData(typing.TypedDict):
    id: str
    project_id: str
    task_x: int
    task_y: int
    task_z: int
    no_count: int
    yes_count: int
    maybe_count: int
    bad_imagery_count: int
    no_share: float
    yes_share: float
    maybe_share: float
    bad_imagery_share: float
    wkt: str


class YesResult(ProjectData):
    my_group_id: int


def delete_if_exists(filename: Path):
    if Path.exists(filename):
        # TODO: This was used before: driver.DeleteDataSource(filename.name)
        filename.unlink()


def create_group_geom(
    group_data: dict[str, YesResult],
    shape: str = "bounding_box",
):
    """Create bounding box or convex hull of input task geometries."""

    result_geom_collection = ogr.Geometry(ogr.wkbMultiPolygon)
    for _, data in group_data.items():
        result_geom = ogr.CreateGeometryFromWkt(data["wkt"])
        result_geom_collection.AddGeometry(result_geom)

    if shape == "convex_hull":
        group_geom = result_geom_collection.ConvexHull()
    elif shape == "bounding_box":
        # Get Envelope
        lon_left, lon_right, lat_top, lat_bottom = result_geom_collection.GetEnvelope()

        # Create Geometry
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(lon_left, lat_top)
        ring.AddPoint(lon_right, lat_top)
        ring.AddPoint(lon_right, lat_bottom)
        ring.AddPoint(lon_left, lat_bottom)
        ring.AddPoint(lon_left, lat_top)
        # TODO: Make sure to return 2D geom, currently 3D with z = 0.0
        group_geom = ogr.Geometry(ogr.wkbPolygon)
        group_geom.AddGeometry(ring)
    else:
        raise Exception(f"Unknown shape: {shape}")

    return group_geom


def create_geojson_file_from_dict(
    final_groups_dict: dict[int, dict[str, YesResult]],
    outfile: Path,
):
    """Take output from generate stats and create TM geometries.

    In order to create a GeoJSON file with a coordinate precision of 7
    we take a small detour.
    First, we create a GeoJSONSeq file.
    This contains only the features.
    Then we add these features to the final GeoJSON file.
    The current shape of the output geometries is set to 'bounding_box'.
    """

    driver = ogr.GetDriverByName("GeoJSONSeq")
    # define spatial Reference
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    outfile_temp = Path(outfile.name.replace(".geojson", "_temp.geojson"))

    delete_if_exists(outfile_temp)
    delete_if_exists(outfile)

    dataSource = driver.CreateDataSource(outfile_temp.name)
    # create layer
    layer = dataSource.CreateLayer(
        outfile_temp.name,
        srs,
        geom_type=ogr.wkbPolygon,
    )

    # create fields
    field_id = ogr.FieldDefn("group_id", ogr.OFTInteger)
    layer.CreateField(field_id)

    if len(final_groups_dict) < 1:
        logger.info("there are no geometries to save")
    else:
        for group_id, _data in final_groups_dict.items():
            group_data = _data
            # create the final group geometry
            group_geom = create_group_geom(group_data, "bounding_box")

            # FIXME: Not sure why mutating _data
            _data["group_geom"] = group_geom  # type: ignore[reportArgumentType]

            # init feature

            if group_geom.GetGeometryName() == "POLYGON":
                featureDefn = layer.GetLayerDefn()
                feature = ogr.Feature(featureDefn)
                # create polygon from wkt and set geometry
                feature.SetGeometry(group_geom)
                # set other attributes
                feature.SetField("group_id", group_id)
                # add feature to layer
                layer.CreateFeature(feature)
                feature.Destroy  # noqa: B018  TODO: Any fix for this?
            elif group_geom.GetGeometryName() == "MULTIPOLYGON":
                for _ in group_geom:
                    featureDefn = layer.GetLayerDefn()
                    feature = ogr.Feature(featureDefn)
                    # create polygon from wkt and set geometry
                    feature.SetGeometry(group_geom)
                    # set other attributes
                    feature.SetField("group_id", group_id)
                    # add feature to layer
                    layer.CreateFeature(feature)
                    feature.Destroy  # noqa: B018  TODO: Any fix for this?
            else:
                logger.info("other geometry type: %s: %s", group_geom.GetGeometryName(), group_geom)
                continue

    # make sure to close layer and data source
    layer = None
    dataSource = None

    # load the features from temp file
    feature_collection = []
    with Path.open(outfile_temp) as f:
        for _, line in enumerate(f):
            feature_collection.append(json.loads(line))

    # create final geojson structure
    geojson_structure = {
        "type": "FeatureCollection",
        "name": outfile.name,  # TODO: Need to check this why we have this here?
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
        },
        "features": feature_collection,
    }

    # save to geojson
    with Path.open(outfile, "w") as json_file:
        json.dump(geojson_structure, json_file)
        logger.info("created outfile: %s.", outfile)

    # remove temp file
    delete_if_exists(outfile_temp)


def create_geojson_file(
    geometries: dict,
    outfile: Path,
):
    driver = ogr.GetDriverByName("GeoJSONSeq")
    # define spatial Reference
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    outfile_temp = Path(outfile.name.replace(".geojson", "_temp.geojson"))

    delete_if_exists(outfile_temp)
    delete_if_exists(outfile)

    dataSource = driver.CreateDataSource(outfile_temp.name)
    # create layer
    layer = dataSource.CreateLayer(
        outfile_temp.name,
        srs,
        geom_type=ogr.wkbPolygon,
    )

    # create fields
    field_id = ogr.FieldDefn("id", ogr.OFTInteger)
    layer.CreateField(field_id)

    if not geometries:
        logger.info("there are no geometries to save")
    else:
        for counter, geom in enumerate(geometries):
            # init feature
            featureDefn = layer.GetLayerDefn()
            feature = ogr.Feature(featureDefn)
            # create polygon from wkt and set geometry
            feature.SetGeometry(geom)
            # set other attributes
            # set first id to 1 instead of 0
            feature.SetField("id", counter + 1)
            # add feature to layer
            layer.CreateFeature(feature)

    # make sure to close layer and data source
    layer = None
    dataSource = None

    # load the features from temp file
    feature_collection = []
    with Path.open(outfile_temp) as f:
        for _, line in enumerate(f):
            feature_collection.append(json.loads(line))

    # create final geojson structure
    geojson_structure = {
        "type": "FeatureCollection",
        "name": outfile.name,  # TODO: Need to check this why we have this here?
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
        },
        "features": feature_collection,
    }
    # save to geojson
    with Path.open(outfile, "w") as json_file:
        json.dump(geojson_structure, json_file)
        logger.info("created outfile: %s.", outfile)

    # remove temp file
    delete_if_exists(outfile_temp)

    logger.info("created outfile: %s.", outfile)

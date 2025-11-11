import typing
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from shapely import wkt
from shapely.geometry import Point

from main.config import Config
from utils.spatial_sampling import (
    distance_on_sphere,
    filter_points,
    spatial_sampling,
)

BASE_DIR = Path(__file__).resolve().parent


class TestDistanceCalculations(unittest.TestCase):
    @typing.override
    @classmethod
    def setUpClass(cls):
        with Path(Config.BASE_DIR, "assets/fixtures/mapillary_sequence.csv").open(encoding="utf-8") as file:
            df = pd.read_csv(file)
            df["geometry"] = df["geometry"].apply(wkt.loads)  # type: ignore[reportArgumentType]
            cls.fixture_df = df

    def test_distance_on_sphere(self):
        p1 = Point(-74.006, 40.7128)
        p2 = Point(-118.2437, 34.0522)

        distance = distance_on_sphere([p1.x, p1.y], [p2.x, p2.y])
        expected_distance = 3940  # Approximate known distance in km

        assert np.isclose(distance, expected_distance, atol=50)

    def test_filter_points(self):
        data = {
            "geometry": [
                "POINT (-74.006 40.7128)",
                "POINT (-75.006 41.7128)",
                "POINT (-76.006 42.7128)",
                "POINT (-77.006 43.7128)",
            ],
        }
        df = pd.DataFrame(data)

        df["geometry"] = df["geometry"].apply(wkt.loads)  # type: ignore[reportArgumentType]

        df["long"] = df["geometry"].apply(
            lambda geom: geom.x if isinstance(geom, Point) else None,
        )
        df["lat"] = df["geometry"].apply(
            lambda geom: geom.y if isinstance(geom, Point) else None,
        )
        threshold_distance = 200
        filtered_df = filter_points(df, threshold_distance)

        assert isinstance(filtered_df, pd.DataFrame)
        assert len(filtered_df) <= len(df)

    def test_spatial_sampling_ordering(self):
        data = {
            "geometry": [
                "POINT (-74.006 40.7128)",
                "POINT (-75.006 41.7128)",
                "POINT (-76.006 42.7128)",
                "POINT (-77.006 43.7128)",
            ],
            "captured_at": [1, 2, 3, 4],
            "sequence_id": ["1", "1", "1", "1"],
        }
        df = pd.DataFrame(data)
        df["geometry"] = df["geometry"].apply(wkt.loads)  # type: ignore[reportArgumentType]

        interval_length = 100
        filtered_gdf = spatial_sampling(df=df, interval_length=interval_length)

        assert filtered_gdf["captured_at"].is_monotonic_decreasing

    def test_spatial_sampling_with_sequence(self):
        threshold_distance = 10
        filtered_df = spatial_sampling(df=self.fixture_df, interval_length=threshold_distance)
        assert isinstance(filtered_df, pd.DataFrame)
        assert len(filtered_df) < len(self.fixture_df)

        filtered_df.reset_index(drop=True, inplace=True)
        for i in range(len(filtered_df) - 1):
            geom1 = filtered_df.loc[i, "geometry"]
            geom2 = filtered_df.loc[i + 1, "geometry"]

            distance = geom1.distance(geom2)  # type: ignore[reportAttributeAccessIssue]

            assert distance < threshold_distance

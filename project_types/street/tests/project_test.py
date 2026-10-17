import json
import unittest
from unittest.mock import MagicMock, patch

from project_types.street.project import StreetProject
from utils.geo.street_image_provider.models import StreetImageProviderNameEnum

AOI_GEOJSON = {
    "type": "Feature",
    "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
    "properties": {},
}


def make_street_project(image_provider: dict[str, str]) -> StreetProject:
    project = MagicMock()
    project.project_type_specifics = {
        "aoi_geometry": "1",
        "mapillary_image_filters": {"organization_id": "42", "creator_id": "7"},
        "image_provider": image_provider,
    }
    aoi_asset = project.aoi_geometry_input_asset
    aoi_asset.asset_type_specifics = {"bbox": (0, 0, 1, 1), "center": (0.5, 0.5), "area": 1}
    aoi_asset.file.open.return_value.__enter__.return_value.read.return_value = json.dumps(AOI_GEOJSON)
    return StreetProject(project)


class TestStreetProject(unittest.TestCase):
    @patch("project_types.street.project.get_image_metadata")
    def test_validate_organization_id_only_for_mapillary(self, mock_get_image_metadata):  # type: ignore[reportMissingParameterType]
        cases = [
            ({"name": StreetImageProviderNameEnum.MAPILLARY.value}, "42"),
            ({"name": StreetImageProviderNameEnum.PANORAMAX.value}, None),
            ({"name": StreetImageProviderNameEnum.PANORAMAX_CUSTOM.value, "url": "https://panoramax.example.com"}, None),
        ]
        for image_provider, expected_organization_id in cases:
            mock_get_image_metadata.reset_mock()
            make_street_project(image_provider).validate()

            mock_get_image_metadata.assert_called_once()
            kwargs = mock_get_image_metadata.call_args.kwargs
            assert kwargs["organization_id"] == expected_organization_id, image_provider
            assert kwargs["creator_id"] == "7"
            assert kwargs["aoi_geojson"] == AOI_GEOJSON

    def test_get_task_specifics_for_firebase_task_id_type(self):
        cases = [
            ({"name": StreetImageProviderNameEnum.MAPILLARY.value}, "123", 123),
            ({"name": StreetImageProviderNameEnum.PANORAMAX.value}, "a1b2c3", "a1b2c3"),
            ({"name": StreetImageProviderNameEnum.PANORAMAX.value}, "123", "123"),
        ]
        for image_provider, firebase_id, expected_task_id in cases:
            task = MagicMock(firebase_id=firebase_id)
            task.task_group.firebase_id = "g1"

            specifics = make_street_project(image_provider).get_task_specifics_for_firebase(task)

            assert specifics.taskId == expected_task_id, image_provider
            assert type(specifics.taskId) is type(expected_task_id), image_provider
            assert specifics.groupId == "g1"

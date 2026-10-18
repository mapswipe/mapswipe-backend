import json
import unittest
from unittest.mock import MagicMock, patch

from project_types.street.project import StreetProject
from utils.geo.street_image_provider.models import StreetImageProviderEnum

AOI_GEOJSON = {
    "type": "Feature",
    "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
    "properties": {},
}


def make_street_project(provider: StreetImageProviderEnum, config: dict[str, str]) -> StreetProject:
    project = MagicMock()
    project.project_type_specifics = {
        "aoi_geometry": "1",
        "provider": provider.value,
        provider.value: config,
    }
    aoi_asset = project.aoi_geometry_input_asset
    aoi_asset.asset_type_specifics = {"bbox": (0, 0, 1, 1), "center": (0.5, 0.5), "area": 1}
    aoi_asset.file.open.return_value.__enter__.return_value.read.return_value = json.dumps(AOI_GEOJSON)
    return StreetProject(project)


class TestStreetProject(unittest.TestCase):
    @patch("project_types.street.project.get_image_metadata")
    def test_validate_organization_id_only_for_mapillary(self, mock_get_image_metadata):  # type: ignore[reportMissingParameterType]
        cases = [
            (StreetImageProviderEnum.MAPILLARY, {"organization_id": "42", "creator_id": "7"}, "42"),
            (StreetImageProviderEnum.PANORAMAX, {"creator_id": "7"}, None),
            (StreetImageProviderEnum.PANORAMAX_CUSTOM, {"creator_id": "7", "url": "https://panoramax.example.com"}, None),
        ]
        for provider, config, expected_organization_id in cases:
            mock_get_image_metadata.reset_mock()
            make_street_project(provider, config).validate()

            mock_get_image_metadata.assert_called_once()
            kwargs = mock_get_image_metadata.call_args.kwargs
            assert kwargs["organization_id"] == expected_organization_id, provider
            assert kwargs["creator_id"] == "7"
            assert kwargs["aoi_geojson"] == AOI_GEOJSON
            assert kwargs["provider"]["name"] == provider

    def test_get_task_specifics_for_firebase_task_id_type(self):
        cases = [
            (StreetImageProviderEnum.MAPILLARY, "123", 123),
            (StreetImageProviderEnum.PANORAMAX, "a1b2c3", "a1b2c3"),
            (StreetImageProviderEnum.PANORAMAX, "123", "123"),
        ]
        for provider, firebase_id, expected_task_id in cases:
            task = MagicMock(firebase_id=firebase_id)
            task.task_group.firebase_id = "g1"

            specifics = make_street_project(provider, {}).get_task_specifics_for_firebase(task)

            assert specifics.taskId == expected_task_id, provider
            assert type(specifics.taskId) is type(expected_task_id), provider
            assert specifics.groupId == "g1"

    def test_get_firebase_image_provider(self):
        cases = [
            (StreetImageProviderEnum.MAPILLARY, {}, {"name": "mapillary", "url": None}),
            (StreetImageProviderEnum.PANORAMAX, {}, {"name": "panoramax", "url": None}),
            (
                StreetImageProviderEnum.PANORAMAX_CUSTOM,
                {"url": "https://panoramax.example.com"},
                {"name": "panoramax_custom", "url": "https://panoramax.example.com"},
            ),
        ]
        for provider, config, expected in cases:
            specifics = make_street_project(provider, config).project_type_specifics
            assert specifics.get_firebase_image_provider().model_dump() == expected, provider

import json
import typing
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from django.core.files.base import ContentFile
from ulid import ULID

from apps.common.models import AssetMimetypeEnum, AssetTypeEnum
from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.project.models import Project, ProjectAsset, ProjectAssetInputTypeEnum, ProjectTypeEnum
from apps.user.factories import UserFactory
from main.tests import TestCase
from project_types.base.project import ValidationException
from project_types.validate.project import ValidateProject
from utils.geo.transform import convert_json_dict_to_geometry_collection, get_area_of_geometry

BASE_DIR = Path(__file__).resolve().parent

OHSOME_FILTER = "building=* and geometry:polygon"
HOT_TM_ID = "4757"

# About 1 sq. km in Kathmandu
HOT_TM_AOI = {
    "type": "MultiPolygon",
    "coordinates": [[[[85.30, 27.70], [85.31, 27.70], [85.31, 27.71], [85.30, 27.71], [85.30, 27.70]]]],
}

OBJECT_GEOJSON_URL = "https://example.com/buildings.geojson"


def _square(lng: float, lat: float, size: float = 0.0001) -> dict[str, typing.Any]:
    return {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[lng, lat], [lng + size, lat], [lng + size, lat + size], [lng, lat + size], [lng, lat]]],
        },
    }


OBJECT_GEOJSON = {
    "type": "FeatureCollection",
    "features": [_square(85.30, 27.70), _square(85.31, 27.70), _square(85.30, 27.71)],
}


TM_SPECIFICS = {
    "object_source": {
        "source_type": "TASKING_MANAGER",
        "tasking_manager_project_id": HOT_TM_ID,
        "ohsome_filter": OHSOME_FILTER,
    },
    "tile_server_property": {"name": "BING", "bing": {"credits": "Bing"}},
}

URL_SPECIFICS = {
    "object_source": {
        "source_type": "OBJECT_GEOJSON_URL",
        "object_geojson_url": OBJECT_GEOJSON_URL,
    },
    "tile_server_property": {"name": "BING", "bing": {"credits": "Bing"}},
}


def _json_response(data: dict[str, typing.Any]) -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = data
    response.text = json.dumps(data)
    return response


class TestValidateObjectSourceTestMutation(TestCase):
    TEST_AOI_OBJECTS = """
        query TestAoiObjects($projectId: ID!, $assetId: ID!, $ohsomeFilter: String!) {
          testAoiObjects(projectId: $projectId, assetId: $assetId, ohsomeFilter: $ohsomeFilter) {
            ok
            error
            objectCount
          }
        }
    """

    TEST_TASKING_MANAGER_PROJECT = """
        mutation TestTaskingManagerProject($projectId: ID!, $hotTmId: String!, $ohsomeFilter: String!) {
          testTaskingManagerProject(projectId: $projectId, hotTmId: $hotTmId, ohsomeFilter: $ohsomeFilter) {
            ... on TestValidateTaskingManagerProjectResponse {
              ok
              error
              objectCount
              hotTmId
              aoiGeometryAsset { id }
            }
          }
        }
    """

    TEST_OBJECT_GEOJSON_URL = """
        mutation TestObjectGeojsonUrl($projectId: ID!, $objectGeojsonUrl: String!) {
          testObjectGeojsonUrl(projectId: $projectId, objectGeojsonUrl: $objectGeojsonUrl) {
            ... on TestValidateObjectGeojsonUrlResponse {
              ok
              error
              objectCount
              objectGeojsonUrl
              aoiGeometryAsset { id }
            }
          }
        }
    """

    PROJECT_LAST_PASSED_TEST = """
        query Project($id: ID!) {
          project(id: $id) {
            aoiGeometryInputAsset { id }
            lastPassedObjectSourceTest {
              aoiGeometryAsset
              objectCount
              testedAt
              inputs {
                sourceType
                aoiGeometry
                taskingManagerProjectId
                objectGeojsonUrl
                ohsomeFilter
              }
            }
          }
        }
    """

    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory.create()
        cls.organization = OrganizationFactory.create(created_by=cls.user, modified_by=cls.user)

    def _create_project(self, **kwargs: typing.Any) -> Project:
        return ProjectFactory.create(
            **{
                "created_by": self.user,
                "modified_by": self.user,
                "requesting_organization": self.organization,
                "project_type": ProjectTypeEnum.VALIDATE,
                **kwargs,
            },
        )

    def _test_tm(self, project: Project, hot_tm_id: str = HOT_TM_ID, object_count: int = 42) -> dict[str, typing.Any]:
        with (
            patch("project_types.validate.project.requests.get", return_value=_json_response(HOT_TM_AOI)),
            patch("project_types.validate.project.get_object_count_from_ohsome", return_value=object_count),
        ):
            content = self.query_check(
                self.TEST_TASKING_MANAGER_PROJECT,
                variables={"projectId": str(project.pk), "hotTmId": hot_tm_id, "ohsomeFilter": OHSOME_FILTER},
            )
        return content["data"]["testTaskingManagerProject"]

    def _test_url(self, project: Project, url: str = OBJECT_GEOJSON_URL) -> dict[str, typing.Any]:
        with patch("project_types.validate.project.requests.get", return_value=_json_response(OBJECT_GEOJSON)):
            content = self.query_check(
                self.TEST_OBJECT_GEOJSON_URL,
                variables={"projectId": str(project.pk), "objectGeojsonUrl": url},
            )
        return content["data"]["testObjectGeojsonUrl"]

    def _get_last_passed_test(self, project: Project) -> dict[str, typing.Any]:
        content = self.query_check(self.PROJECT_LAST_PASSED_TEST, variables={"id": str(project.pk)})
        return content["data"]["project"]

    @staticmethod
    def _aoi_assets(project: Project):
        return ProjectAsset.usable_objects().filter(
            project=project,
            type=AssetTypeEnum.INPUT,
            input_type=ProjectAssetInputTypeEnum.AOI_GEOMETRY,
        )

    def test_tasking_manager_test_stores_aoi_asset(self):
        self.force_login(self.user)
        project = self._create_project()

        resp = self._test_tm(project)
        assert resp["ok"], resp["error"]
        assert resp["objectCount"] == 42

        asset = self._aoi_assets(project).get()
        assert resp["aoiGeometryAsset"]["id"] == str(asset.pk)
        assert asset.mimetype == AssetMimetypeEnum.GEOJSON
        assert asset.created_by == self.user
        assert asset.asset_type_specifics["area"] > 0
        assert asset.file is not None
        with asset.file.open() as f:
            stored = json.loads(f.read())
        assert stored["features"][0]["geometry"]["type"] == "MultiPolygon"

        project_data = self._get_last_passed_test(project)
        assert project_data["aoiGeometryInputAsset"]["id"] == str(asset.pk)
        record = project_data["lastPassedObjectSourceTest"]
        assert record["aoiGeometryAsset"] == str(asset.pk)
        assert record["objectCount"] == 42
        assert record["inputs"] == {
            "sourceType": "TASKING_MANAGER",
            "aoiGeometry": None,
            "taskingManagerProjectId": HOT_TM_ID,
            "objectGeojsonUrl": None,
            "ohsomeFilter": OHSOME_FILTER,
        }

    def test_object_geojson_url_test_stores_convex_hull(self):
        self.force_login(self.user)
        project = self._create_project()

        resp = self._test_url(project)
        assert resp["ok"], resp["error"]
        assert resp["objectCount"] == 3

        asset = self._aoi_assets(project).get()
        assert resp["aoiGeometryAsset"]["id"] == str(asset.pk)
        with asset.file.open() as f:
            stored = json.loads(f.read())
        hull = stored["features"][0]["geometry"]
        assert hull["type"] == "Polygon"
        # The hull spans the three squares
        lngs = [c[0] for c in hull["coordinates"][0]]
        lats = [c[1] for c in hull["coordinates"][0]]
        assert min(lngs) == 85.30
        assert max(lngs) > 85.31
        assert min(lats) == 27.70
        assert max(lats) > 27.71

        record = self._get_last_passed_test(project)["lastPassedObjectSourceTest"]
        assert record["inputs"] == {
            "sourceType": "OBJECT_GEOJSON_URL",
            "aoiGeometry": None,
            "taskingManagerProjectId": None,
            "objectGeojsonUrl": OBJECT_GEOJSON_URL,
            "ohsomeFilter": None,
        }

    def _upload_aoi(self, project: Project) -> ProjectAsset:
        file = ContentFile((BASE_DIR / "data/ring-road.geojson").read_bytes(), "ring-road.geojson")
        return ProjectAsset.objects.create(
            client_id=str(ULID()),
            project=project,
            type=AssetTypeEnum.INPUT,
            input_type=ProjectAssetInputTypeEnum.AOI_GEOMETRY,
            mimetype=AssetMimetypeEnum.GEOJSON,
            file=file,
            file_size=file.size,
            asset_type_specifics={"bbox": [85.28, 27.67, 85.35, 27.74], "center": [85.31, 27.70], "area": 50.0},
            created_by=self.user,
            modified_by=self.user,
        )

    def test_aoi_objects_query_stores_nothing(self):
        self.force_login(self.user)
        project = self._create_project()
        uploaded = self._upload_aoi(project)

        with patch("project_types.validate.project.get_object_count_from_ohsome", return_value=7):
            content = self.query_check(
                self.TEST_AOI_OBJECTS,
                variables={"projectId": str(project.pk), "assetId": str(uploaded.pk), "ohsomeFilter": OHSOME_FILTER},
            )
        resp = content["data"]["testAoiObjects"]
        assert resp["ok"], resp["error"]
        assert resp["objectCount"] == 7

        # The uploaded AOI is already a project asset, so the query records nothing
        assert list(self._aoi_assets(project)) == [uploaded]
        project.refresh_from_db()
        assert project.last_passed_object_source_test is None

    def test_failed_test_keeps_last_passed_test(self):
        self.force_login(self.user)
        project = self._create_project()
        assert self._test_tm(project)["ok"]
        first_asset = self._aoi_assets(project).get()
        project.refresh_from_db()
        first_record = project.last_passed_object_source_test

        # ohsome finds no objects for a different TM project
        resp = self._test_tm(project, hot_tm_id="9999", object_count=0)
        assert not resp["ok"]
        assert resp["error"] == "AOI does not contain objects from selected filter."
        assert resp["aoiGeometryAsset"] is None

        project.refresh_from_db()
        assert project.last_passed_object_source_test == first_record
        assert list(self._aoi_assets(project)) == [first_asset]

    def test_new_passed_test_replaces_previous_generated_asset(self):
        self.force_login(self.user)
        project = self._create_project()
        assert self._test_tm(project)["ok"]
        first_asset = self._aoi_assets(project).get()

        assert self._test_url(project)["ok"]
        second_asset = self._aoi_assets(project).get()
        assert second_asset != first_asset

        first_asset.refresh_from_db()
        assert first_asset.marked_as_deleted

        project.refresh_from_db()
        assert project.aoi_geometry_input_asset == second_asset

    def test_aoi_asset_is_kept_on_save_while_inputs_match(self):
        self.force_login(self.user)
        project = self._create_project()
        assert self._test_tm(project)["ok"]
        asset = self._aoi_assets(project).get()
        project.refresh_from_db()

        specifics = {
            "object_source": {
                "source_type": "TASKING_MANAGER",
                "tasking_manager_project_id": HOT_TM_ID,
                "ohsome_filter": OHSOME_FILTER,
            },
            "tile_server_property": {"name": "BING", "bing": {"credits": "Bing"}},
        }
        project.project_type_specifics = specifics
        assert ValidateProject(project).get_aoi_geometry_asset() == asset

        # Changing an input of the test drops the AOI asset
        project.project_type_specifics = {
            **specifics,
            "object_source": {**specifics["object_source"], "ohsome_filter": "highway=*"},
        }
        assert ValidateProject(project).get_aoi_geometry_asset() is None

        project.project_type_specifics = {
            **specifics,
            "object_source": {**specifics["object_source"], "tasking_manager_project_id": "1"},
        }
        assert ValidateProject(project).get_aoi_geometry_asset() is None

    def test_invalid_url_is_rejected_before_fetching(self):
        self.force_login(self.user)
        project = self._create_project()

        with patch("project_types.validate.project.requests.get") as mock_get:
            content = self.query_check(
                self.TEST_OBJECT_GEOJSON_URL,
                variables={"projectId": str(project.pk), "objectGeojsonUrl": "not a url"},
            )
        resp = content["data"]["testObjectGeojsonUrl"]
        assert not resp["ok"]
        assert resp["error"].startswith("Invalid object source")
        mock_get.assert_not_called()
        assert not self._aoi_assets(project).exists()

    def test_only_draft_or_failed_validate_projects_can_be_tested(self):
        self.force_login(self.user)

        find_project = self._create_project(project_type=ProjectTypeEnum.FIND)
        resp = self._test_tm(find_project)
        assert not resp["ok"]
        assert resp["error"] == "Object source tests are only available for Validate projects"

        processed_project = self._create_project(status=Project.Status.PROCESSED)
        resp = self._test_tm(processed_project)
        assert not resp["ok"]
        assert resp["error"] == "Cannot test the object source of a project with status Processed"

        failed_project = self._create_project(status=Project.Status.PROCESSING_FAILED)
        assert self._test_tm(failed_project)["ok"]

        for project in (find_project, processed_project):
            assert not self._aoi_assets(project).exists()

    UPDATE_PROJECT_STATUS = """
        mutation UpdateProjectStatus($pk: ID!, $data: ProjectStatusUpdateInput!) {
          updateProjectStatus(pk: $pk, data: $data) {
            ... on ProjectTypeMutationResponseType {
              errors
              ok
              result { status }
            }
          }
        }
    """

    def _process(self, project: Project) -> dict[str, typing.Any]:
        content = self.query_check(
            self.UPDATE_PROJECT_STATUS,
            variables={"pk": str(project.pk), "data": {"clientId": project.client_id, "status": "READY_TO_PROCESS"}},
        )
        return content["data"]["updateProjectStatus"]

    @staticmethod
    def _error_messages(resp: dict[str, typing.Any]) -> str:
        return " ".join(str(error["messages"]) for error in resp["errors"])

    def _save_specifics(self, project: Project, specifics: dict[str, typing.Any]):
        project.project_type_specifics = specifics
        project.save(update_fields=["project_type_specifics"])

    def test_processing_is_refused_without_a_passed_test(self):
        self.force_login(self.user)
        project = self._create_project(project_type_specifics=TM_SPECIFICS)

        resp = self._process(project)
        assert not resp["ok"]
        assert "testTaskingManagerProject" in self._error_messages(resp)
        project.refresh_from_db()
        assert project.status_enum == Project.Status.DRAFT

    def test_processing_is_refused_when_inputs_changed_since_test(self):
        self.force_login(self.user)
        project = self._create_project()
        assert self._test_url(project)["ok"]
        project.refresh_from_db()
        self._save_specifics(
            project,
            {
                **URL_SPECIFICS,
                "object_source": {
                    **URL_SPECIFICS["object_source"],
                    "object_geojson_url": "https://example.com/other.geojson",
                },
            },
        )

        resp = self._process(project)
        assert not resp["ok"]
        assert "testObjectGeojsonUrl" in self._error_messages(resp)

        # Testing the other source type does not unlock it either
        self._save_specifics(project, TM_SPECIFICS)
        resp = self._process(project)
        assert not resp["ok"]
        assert "testTaskingManagerProject" in self._error_messages(resp)

    def test_processing_is_allowed_when_inputs_match_test(self):
        self.force_login(self.user)
        project = self._create_project()
        assert self._test_tm(project)["ok"]
        project.refresh_from_db()
        self._save_specifics(project, TM_SPECIFICS)

        resp = self._process(project)
        assert resp["ok"], resp["errors"]
        assert resp["result"]["status"] == "READY_TO_PROCESS"

    def test_tasking_manager_processing_uses_stored_aoi(self):
        self.force_login(self.user)
        project = self._create_project()
        assert self._test_tm(project)["ok"]
        project.refresh_from_db()
        self._save_specifics(project, TM_SPECIFICS)

        with (
            patch("project_types.validate.project.requests.get") as mock_get,
            patch("project_types.validate.project.get_objects_from_ohsome", return_value=OBJECT_GEOJSON) as mock_ohsome,
        ):
            features = ValidateProject(project).validate()

        # The AOI is not fetched again from HOT Tasking Manager
        mock_get.assert_not_called()
        assert len(features) == 3
        aoi_sent_to_ohsome = mock_ohsome.call_args.args[0]
        assert aoi_sent_to_ohsome["type"] in ("Polygon", "MultiPolygon")

        project.refresh_from_db()
        assert project.aoi_geometry is not None
        assert project.aoi_geometry.geometry is not None
        assert project.aoi_geometry.geometry.extent == (85.30, 27.70, 85.31, 27.71)

    def test_object_geojson_url_processing_uses_stored_hull_as_area(self):
        self.force_login(self.user)
        project = self._create_project()
        assert self._test_url(project)["ok"]
        project.refresh_from_db()
        self._save_specifics(project, URL_SPECIFICS)
        hull_extent = (85.30, 27.70, 85.3101, 27.7101)

        with patch("project_types.validate.project.requests.get", return_value=_json_response(OBJECT_GEOJSON)):
            features = ValidateProject(project).validate()

        assert len(features) == 3
        project.refresh_from_db()
        assert project.aoi_geometry is not None
        assert project.aoi_geometry.geometry is not None
        assert project.aoi_geometry.geometry.extent == pytest.approx(hull_extent)

        # The total area is the area of the objects, not of the hull
        _, objects = convert_json_dict_to_geometry_collection(OBJECT_GEOJSON)
        total_area = project.aoi_geometry.total_area
        assert total_area is not None
        assert total_area == pytest.approx(get_area_of_geometry(objects))
        assert total_area < get_area_of_geometry(project.aoi_geometry.geometry)

    def test_processing_fails_without_stored_aoi(self):
        project = self._create_project(project_type_specifics=TM_SPECIFICS)

        with pytest.raises(ValidationException, match="testTaskingManagerProject"):
            ValidateProject(project).validate()

    def test_aoi_file_project_is_processed_without_a_passed_test(self):
        self.force_login(self.user)
        project = self._create_project()
        uploaded = self._upload_aoi(project)
        self._save_specifics(
            project,
            {
                "object_source": {
                    "source_type": "AOI_GEOJSON_FILE",
                    "aoi_geometry": str(uploaded.pk),
                    "ohsome_filter": OHSOME_FILTER,
                },
                "tile_server_property": {"name": "BING", "bing": {"credits": "Bing"}},
            },
        )
        assert project.last_passed_object_source_test is None

        resp = self._process(project)
        assert resp["ok"], resp["errors"]
        assert resp["result"]["status"] == "READY_TO_PROCESS"

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
from utils.geo.transform import (
    convert_json_dict_to_aoi_geometry,
    convert_json_dict_to_geometry_collection,
    get_area_of_geometry,
)

BASE_DIR = Path(__file__).resolve().parent

OHSOME_FILTER = "building=* and geometry:polygon"
HOT_TM_ID = "4757"

# About 1 sq. km in Kathmandu
HOT_TM_AOI = {
    "type": "MultiPolygon",
    "coordinates": [[[[85.30, 27.70], [85.31, 27.70], [85.31, 27.71], [85.30, 27.71], [85.30, 27.70]]]],
}

OBJECT_GEOJSON_URL = "https://example.com/buildings.geojson"
# NOTE: The encoded characters are part of the signature and must reach the server as given
PRESIGNED_OBJECT_GEOJSON_URL = (
    "https://bucket.s3.amazonaws.com/buildings.geojson"
    "?X-Amz-Credential=AKIA%2F20261127%2Fus-east-1%2Fs3%2Faws4_request"
    "&X-Amz-Signature=ab%2Bcd%3D%3D&X-Amz-Expires=3600"
)


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

# NOTE: The convex hull of these objects is larger than the AOI limit of 2500 sq. km
SPREAD_OBJECT_GEOJSON = {
    "type": "FeatureCollection",
    "features": [_square(85.0, 27.0), _square(85.6, 27.0), _square(85.0, 27.6), _square(85.6, 27.6)],
}

TILE_SERVER_INPUT = {"name": "BING", "bing": {"credits": "Bing"}}

TM_SOURCE = {
    "sourceType": "TASKING_MANAGER",
    "taskingManagerProjectId": HOT_TM_ID,
    "ohsomeFilter": OHSOME_FILTER,
}

URL_SOURCE = {
    "sourceType": "OBJECT_GEOJSON_URL",
    "objectGeojsonUrl": OBJECT_GEOJSON_URL,
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
              aoiGeometryAsset { id markedAsDeleted }
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
              aoiGeometryAsset { id markedAsDeleted }
            }
          }
        }
    """

    UPDATE_PROJECT = """
        mutation UpdateProject($pk: ID!, $data: ProjectUpdateInput!) {
          updateProject(pk: $pk, data: $data) {
            ... on ProjectTypeMutationResponseType {
              errors
              ok
              result { id }
            }
          }
        }
    """

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

    def _test_url(
        self,
        project: Project,
        url: str = OBJECT_GEOJSON_URL,
        objects: dict[str, typing.Any] = OBJECT_GEOJSON,
    ) -> dict[str, typing.Any]:
        with patch("project_types.validate.project.requests.get", return_value=_json_response(objects)):
            content = self.query_check(
                self.TEST_OBJECT_GEOJSON_URL,
                variables={"projectId": str(project.pk), "objectGeojsonUrl": url},
            )
        return content["data"]["testObjectGeojsonUrl"]

    def _save(self, project: Project, object_source: dict[str, typing.Any]) -> dict[str, typing.Any]:
        """Save the project as the dashboard does, with the AOI asset in object_source.aoiGeometry."""
        content = self.query_check(
            self.UPDATE_PROJECT,
            variables={
                "pk": str(project.pk),
                "data": {
                    "clientId": project.client_id,
                    "projectTypeSpecifics": {
                        "validate": {
                            "objectSource": object_source,
                            "tileServerProperty": TILE_SERVER_INPUT,
                        },
                    },
                },
            },
        )
        resp = content["data"]["updateProject"]
        project.refresh_from_db()
        return resp

    def _process(self, project: Project) -> dict[str, typing.Any]:
        content = self.query_check(
            self.UPDATE_PROJECT_STATUS,
            variables={"pk": str(project.pk), "data": {"clientId": project.client_id, "status": "READY_TO_PROCESS"}},
        )
        return content["data"]["updateProjectStatus"]

    @staticmethod
    def _aoi_assets(project: Project):
        # NOTE: Includes the assets of unsaved tests, which are marked as deleted
        return ProjectAsset.objects.filter(
            project=project,
            type=AssetTypeEnum.INPUT,
            input_type=ProjectAssetInputTypeEnum.AOI_GEOMETRY,
        )

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

    # Tests

    def test_tasking_manager_test_stores_temporary_aoi_asset(self):
        self.force_login(self.user)
        project = self._create_project()
        modified_at = project.modified_at

        resp = self._test_tm(project)
        assert resp["ok"], resp["error"]
        assert resp["objectCount"] == 42

        asset = self._aoi_assets(project).get()
        assert resp["aoiGeometryAsset"] == {"id": str(asset.pk), "markedAsDeleted": True}
        assert asset.marked_as_deleted
        # Hidden from the other asset lookups until a save uses it
        assert not ProjectAsset.usable_objects().filter(pk=asset.pk).exists()
        assert asset.mimetype == AssetMimetypeEnum.GEOJSON
        assert asset.created_by == self.user
        assert asset.asset_type_specifics["area"] > 0
        assert asset.file is not None
        with asset.file.open() as f:
            stored = json.loads(f.read())
        assert stored["features"][0]["geometry"]["type"] == "MultiPolygon"

        # The test does not change the project
        project.refresh_from_db()
        assert project.aoi_geometry_input_asset is None
        assert project.aoi_geometry is None
        assert project.modified_at == modified_at

    def test_object_geojson_url_test_stores_convex_hull(self):
        self.force_login(self.user)
        project = self._create_project()

        resp = self._test_url(project)
        assert resp["ok"], resp["error"]
        assert resp["objectCount"] == 3

        asset = self._aoi_assets(project).get()
        assert resp["aoiGeometryAsset"] == {"id": str(asset.pk), "markedAsDeleted": True}
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

        project.refresh_from_db()
        assert project.aoi_geometry_input_asset is None

    def test_object_geojson_url_test_rejects_hull_larger_than_aoi_limit(self):
        self.force_login(self.user)
        project = self._create_project()

        resp = self._test_url(project, objects=SPREAD_OBJECT_GEOJSON)
        assert not resp["ok"]
        assert resp["error"] == "Area for AOI Geometry must be less than 2500 sq. km"
        assert not self._aoi_assets(project).exists()

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

        # The uploaded AOI is already a project asset, so the query stores nothing
        assert list(self._aoi_assets(project)) == [uploaded]

    def test_failed_test_stores_no_asset(self):
        self.force_login(self.user)
        project = self._create_project()

        # ohsome finds no objects
        resp = self._test_tm(project, object_count=0)
        assert not resp["ok"]
        assert resp["error"] == "AOI does not contain objects from selected filter."
        assert resp["aoiGeometryAsset"] is None
        assert not self._aoi_assets(project).exists()

    def test_tests_do_not_change_a_saved_project(self):
        self.force_login(self.user)
        project = self._create_project()
        uploaded = self._upload_aoi(project)
        aoi_file_source = {"sourceType": "AOI_GEOJSON_FILE", "aoiGeometry": str(uploaded.pk), "ohsomeFilter": OHSOME_FILTER}
        resp = self._save(project, aoi_file_source)
        assert resp["ok"], resp["errors"]
        saved_specifics = project.project_type_specifics
        assert project.aoi_geometry_input_asset == uploaded

        # Test other sources in the form without saving them
        assert self._test_tm(project)["ok"]
        assert self._test_url(project)["ok"]
        assert self._test_tm(project)["ok"]

        project.refresh_from_db()
        assert project.aoi_geometry_input_asset == uploaded
        assert project.project_type_specifics == saved_specifics
        uploaded.refresh_from_db()
        assert not uploaded.marked_as_deleted
        # Each test keeps its own asset, marked as deleted
        assert self._aoi_assets(project).filter(marked_as_deleted=True).count() == 3

        # Processing uses the saved AOI file, not the AOI of a test
        with (
            patch("project_types.validate.project.requests.get") as mock_get,
            patch("project_types.validate.project.get_object_count_from_ohsome", return_value=3),
            patch("project_types.validate.project.get_objects_from_ohsome", return_value=OBJECT_GEOJSON) as mock_ohsome,
        ):
            features = ValidateProject(project).validate()

        mock_get.assert_not_called()
        assert len(features) == 3
        with uploaded.file.open() as f:
            uploaded_aoi = convert_json_dict_to_aoi_geometry(json.loads(f.read()))
        assert mock_ohsome.call_args.args[0] == uploaded_aoi

    def test_save_attaches_test_asset_and_makes_it_permanent(self):
        self.force_login(self.user)
        project = self._create_project()
        asset_id = self._test_tm(project)["aoiGeometryAsset"]["id"]

        resp = self._save(project, {**TM_SOURCE, "aoiGeometry": asset_id})
        assert resp["ok"], resp["errors"]

        asset = ProjectAsset.objects.get(pk=asset_id)
        assert not asset.marked_as_deleted
        assert project.aoi_geometry_input_asset == asset
        assert project.aoi_geometry is not None
        assert project.aoi_geometry.geometry is not None
        assert project.aoi_geometry.geometry.extent == (85.30, 27.70, 85.31, 27.71)
        assert project.total_area == pytest.approx(asset.asset_type_specifics["area"])

    def test_aoi_geometry_asset_excludes_marked_as_deleted_by_default(self):
        self.force_login(self.user)
        project = self._create_project()
        asset_id = self._test_tm(project)["aoiGeometryAsset"]["id"]
        # NOTE: The object source references the test asset, which no save has used yet
        project.project_type_specifics = {
            "object_source": {
                "source_type": "TASKING_MANAGER",
                "tasking_manager_project_id": HOT_TM_ID,
                "ohsome_filter": OHSOME_FILTER,
                "aoi_geometry": asset_id,
            },
            "tile_server_property": {"name": "BING", "bing": {"credits": "Bing"}},
        }
        handler = ValidateProject(project)

        with pytest.raises(ProjectAsset.DoesNotExist):
            handler.get_aoi_geometry_asset()
        asset = handler.get_aoi_geometry_asset(include_marked_as_deleted=True)
        assert asset is not None
        assert str(asset.pk) == asset_id

    def test_object_geojson_url_project_area_is_the_hull_area(self):
        self.force_login(self.user)
        project = self._create_project()
        asset_id = self._test_url(project)["aoiGeometryAsset"]["id"]

        resp = self._save(project, {**URL_SOURCE, "aoiGeometry": asset_id})
        assert resp["ok"], resp["errors"]

        _, objects = convert_json_dict_to_geometry_collection(OBJECT_GEOJSON)
        assert project.aoi_geometry is not None
        assert project.aoi_geometry.geometry is not None
        total_area = project.aoi_geometry.total_area
        assert total_area is not None
        assert total_area == pytest.approx(get_area_of_geometry(project.aoi_geometry.geometry))
        assert total_area > get_area_of_geometry(objects)

    def test_presigned_url_is_fetched_as_given(self):
        self.force_login(self.user)
        project = self._create_project()

        with patch("project_types.validate.project.requests.get", return_value=_json_response(OBJECT_GEOJSON)) as mock_get:
            content = self.query_check(
                self.TEST_OBJECT_GEOJSON_URL,
                variables={"projectId": str(project.pk), "objectGeojsonUrl": PRESIGNED_OBJECT_GEOJSON_URL},
            )
        resp = content["data"]["testObjectGeojsonUrl"]
        assert resp["ok"], resp["error"]
        assert mock_get.call_args.args[0] == PRESIGNED_OBJECT_GEOJSON_URL

        # Processing fetches the saved URL as given too
        url_source = {**URL_SOURCE, "objectGeojsonUrl": PRESIGNED_OBJECT_GEOJSON_URL}
        assert self._save(project, {**url_source, "aoiGeometry": resp["aoiGeometryAsset"]["id"]})["ok"]
        with patch("project_types.validate.project.requests.get", return_value=_json_response(OBJECT_GEOJSON)) as mock_get:
            ValidateProject(project).validate()
        assert mock_get.call_args.args[0] == PRESIGNED_OBJECT_GEOJSON_URL

    def test_url_is_fetched_without_surrounding_whitespace(self):
        self.force_login(self.user)
        project = self._create_project()

        with patch("project_types.validate.project.requests.get", return_value=_json_response(OBJECT_GEOJSON)) as mock_get:
            content = self.query_check(
                self.TEST_OBJECT_GEOJSON_URL,
                variables={"projectId": str(project.pk), "objectGeojsonUrl": f"  {PRESIGNED_OBJECT_GEOJSON_URL} "},
            )
        resp = content["data"]["testObjectGeojsonUrl"]
        assert resp["ok"], resp["error"]
        assert mock_get.call_args.args[0] == PRESIGNED_OBJECT_GEOJSON_URL

    def test_unknown_project_id_is_rejected(self):
        self.force_login(self.user)
        for project_id in ("not-a-number", "999999"):
            content = self.query_check(
                self.TEST_OBJECT_GEOJSON_URL,
                variables={"projectId": project_id, "objectGeojsonUrl": OBJECT_GEOJSON_URL},
            )
            resp = content["data"]["testObjectGeojsonUrl"]
            assert not resp["ok"]
            assert resp["error"] == "Project does not exist"

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

    def test_processing_is_allowed_with_a_saved_aoi(self):
        self.force_login(self.user)
        project = self._create_project()
        asset_id = self._test_tm(project)["aoiGeometryAsset"]["id"]
        assert self._save(project, {**TM_SOURCE, "aoiGeometry": asset_id})["ok"]

        resp = self._process(project)
        assert resp["ok"], resp["errors"]
        assert resp["result"]["status"] == "READY_TO_PROCESS"

    def test_aoi_file_project_is_processed_with_its_uploaded_aoi(self):
        self.force_login(self.user)
        project = self._create_project()
        uploaded = self._upload_aoi(project)
        resp = self._save(
            project,
            {"sourceType": "AOI_GEOJSON_FILE", "aoiGeometry": str(uploaded.pk), "ohsomeFilter": OHSOME_FILTER},
        )
        assert resp["ok"], resp["errors"]

        resp = self._process(project)
        assert resp["ok"], resp["errors"]
        assert resp["result"]["status"] == "READY_TO_PROCESS"

    def test_tasking_manager_processing_uses_saved_aoi(self):
        self.force_login(self.user)
        project = self._create_project()
        asset_id = self._test_tm(project)["aoiGeometryAsset"]["id"]
        assert self._save(project, {**TM_SOURCE, "aoiGeometry": asset_id})["ok"]
        aoi_geometry = project.aoi_geometry

        with (
            patch("project_types.validate.project.requests.get") as mock_get,
            patch("project_types.validate.project.get_object_count_from_ohsome", return_value=3),
            patch("project_types.validate.project.get_objects_from_ohsome", return_value=OBJECT_GEOJSON) as mock_ohsome,
        ):
            features = ValidateProject(project).validate()

        # The AOI is not fetched again from HOT Tasking Manager
        mock_get.assert_not_called()
        assert len(features) == 3
        aoi_sent_to_ohsome = mock_ohsome.call_args.args[0]
        assert aoi_sent_to_ohsome["type"] in ("Polygon", "MultiPolygon")

        # The project area set on save is kept
        project.refresh_from_db()
        assert project.aoi_geometry == aoi_geometry

    def test_tasking_manager_processing_checks_object_count_before_download(self):
        self.force_login(self.user)
        project = self._create_project()
        asset_id = self._test_tm(project)["aoiGeometryAsset"]["id"]
        assert self._save(project, {**TM_SOURCE, "aoiGeometry": asset_id})["ok"]

        with (
            patch("project_types.validate.project.get_object_count_from_ohsome", return_value=0),
            patch("project_types.validate.project.get_objects_from_ohsome") as mock_ohsome,
            pytest.raises(ValidationException, match=r"AOI does not contain objects from selected filter\."),
        ):
            ValidateProject(project).validate()
        mock_ohsome.assert_not_called()

    def test_object_geojson_url_processing_uses_saved_hull(self):
        self.force_login(self.user)
        project = self._create_project()
        asset_id = self._test_url(project)["aoiGeometryAsset"]["id"]
        assert self._save(project, {**URL_SOURCE, "aoiGeometry": asset_id})["ok"]
        total_area = project.total_area
        hull_extent = (85.30, 27.70, 85.3101, 27.7101)

        with patch("project_types.validate.project.requests.get", return_value=_json_response(OBJECT_GEOJSON)):
            features = ValidateProject(project).validate()

        assert len(features) == 3
        project.refresh_from_db()
        assert project.aoi_geometry is not None
        assert project.aoi_geometry.geometry is not None
        assert project.aoi_geometry.geometry.extent == pytest.approx(hull_extent)
        assert project.total_area == total_area

    def test_processing_fails_without_saved_aoi(self):
        project = self._create_project()
        project.project_type_specifics = {
            "object_source": {
                "source_type": "TASKING_MANAGER",
                "tasking_manager_project_id": HOT_TM_ID,
                "ohsome_filter": OHSOME_FILTER,
            },
            "tile_server_property": {"name": "BING", "bing": {"credits": "Bing"}},
        }

        with pytest.raises(ValidationException, match="AOI Geometry is missing"):
            ValidateProject(project).validate()

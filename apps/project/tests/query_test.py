import typing

from django.test import override_settings

from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.project.models import Project, ProjectStatusEnum, ProjectTypeEnum
from apps.user.factories import UserFactory
from main.settings import STRAWBERRY_DJANGO
from main.tests import TestCase
from utils.common import format_object_keys, to_camel_case


class TestProjectQuery(TestCase):
    class Query:
        PROJECTS = """
            fragment VectorTileServerPropertyFields on ProjectVectorTileServerConfig {
                name
                custom {
                  credits
                  sourceLayer
                  url
                  minZoom
                  maxZoom
                }
                openFreeMap {
                  credits
                  sourceLayer
                }
                openStreetMap {
                  credits
                  sourceLayer
                }
                versatiles {
                  credits
                  sourceLayer
                }
            }
            fragment RasterTileServerPropertyFields on ProjectRasterTileServerConfig {
              name
              bing {
                credits
              }
              custom {
                credits
                url
              }
              esri {
                credits
              }
              esriBeta {
                credits
              }
              mapbox {
                credits
              }
              maxarPremium {
                credits
              }
              maxarStandard {
                credits
              }
            }
            query Projects($pagination: OffsetPaginationInput, $includeAll: Boolean = false) {
              projects(order: {id: ASC}, pagination: $pagination, includeAll: $includeAll) {
                totalCount
                pageInfo {
                  offset
                  limit
                }
                results {
                  id
                  name
                  topic
                  region
                  projectNumber
                  projectType
                  projectTypeSpecifics {
                    ... on FindProjectPropertyType {
                      zoomLevel
                      aoiGeometry
                      tileServerProperty {
                        ...RasterTileServerPropertyFields
                      }
                    }
                    ... on CompareProjectPropertyType {
                      zoomLevel
                      aoiGeometry
                      tileServerProperty {
                        ...RasterTileServerPropertyFields
                      }
                      tileServerBProperty {
                        ...RasterTileServerPropertyFields
                      }
                    }
                    ... on CompletenessProjectPropertyType {
                      zoomLevel
                      aoiGeometry
                      tileServerProperty {
                        ...RasterTileServerPropertyFields
                      }
                      overlayTileServerProperty {
                        type
                        vector {
                          circleColor
                          circleOpacity
                          circleRadius
                          fillColor
                          fillOpacity
                          lineColor
                          lineDasharray
                          lineOpacity
                          lineWidth
                          tileServer {
                              ...VectorTileServerPropertyFields
                          }
                        }
                        raster {
                          opacity
                          tileServer {
                              ...RasterTileServerPropertyFields
                          }
                        }
                      }
                    }
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
        cls.user_resource_kwargs = dict(
            created_by=cls.user,
            modified_by=cls.user,
        )

        cls.organization = OrganizationFactory.create(**cls.user_resource_kwargs)
        # Some init projects
        cls.projects = [
            ProjectFactory.create(
                **cls.user_resource_kwargs,
                topic="Test Topic 1",
                region="Test Region 1",
                project_number=1,
                requesting_organization=cls.organization,
                project_type=ProjectTypeEnum.FIND,
                project_type_specifics={
                    "zoom_level": 14,
                    "aoi_geometry": "1",
                    "tile_server_property": {
                        "name": "BING",
                        "custom": None,
                        "bing": {
                            "credits": "My Map",
                        },
                        "mapbox": None,
                        "maxar_standard": None,
                        "maxar_premium": None,
                        "esri": None,
                        "esri_beta": None,
                    },
                },
            ),
            ProjectFactory.create(
                **cls.user_resource_kwargs,
                topic="Test Topic 2",
                region="Test Region 2",
                project_number=1,
                requesting_organization=cls.organization,
                project_type=ProjectTypeEnum.COMPARE,
                project_type_specifics={
                    "zoom_level": 14,
                    "aoi_geometry": "1",
                    "tile_server_property": {
                        "name": "BING",
                        "custom": None,
                        "bing": {
                            "credits": "My Map",
                        },
                        "mapbox": None,
                        "maxar_standard": None,
                        "maxar_premium": None,
                        "esri": None,
                        "esri_beta": None,
                    },
                    "tile_server_b_property": {
                        "name": "ESRI",
                        "custom": None,
                        "bing": None,
                        "mapbox": None,
                        "maxar_standard": None,
                        "maxar_premium": None,
                        "esri": {
                            "credits": "My Map",
                        },
                        "esri_beta": None,
                    },
                },
            ),
            ProjectFactory.create(
                **cls.user_resource_kwargs,
                topic="Test Topic 3",
                region="Test Region 3",
                project_number=1,
                requesting_organization=cls.organization,
                project_type=ProjectTypeEnum.COMPLETENESS,
                project_type_specifics={
                    "zoom_level": 14,
                    "aoi_geometry": "1",
                    "tile_server_property": {
                        "name": "BING",
                        "custom": None,
                        "bing": {
                            "credits": "My Map",
                        },
                        "mapbox": None,
                        "maxar_standard": None,
                        "maxar_premium": None,
                        "esri": None,
                        "esri_beta": None,
                    },
                    "overlay_tile_server_property": {
                        "type": "RASTER_TILE",
                        "vector": None,
                        "raster": {
                            "opacity": 1.0,
                            "tile_server": {
                                "name": "CUSTOM",
                                "custom": {
                                    "url": "https://hi-there/{x}/{y}/{z}",
                                    "credits": "My Map",
                                },
                                "bing": None,
                                "mapbox": None,
                                "maxar_standard": None,
                                "maxar_premium": None,
                                "esri": None,
                                "esri_beta": None,
                            },
                        },
                    },
                },
            ),
            ProjectFactory.create(
                **cls.user_resource_kwargs,
                topic="Test Topic 4",
                region="Test Region 4",
                project_number=1,
                requesting_organization=cls.organization,
                project_type=ProjectTypeEnum.COMPLETENESS,
                project_type_specifics={
                    "zoom_level": 14,
                    "aoi_geometry": "1",
                    "tile_server_property": {
                        "name": "BING",
                        "custom": None,
                        "bing": {
                            "credits": "My Map",
                        },
                        "mapbox": None,
                        "maxar_standard": None,
                        "maxar_premium": None,
                        "esri": None,
                        "esri_beta": None,
                    },
                    "overlay_tile_server_property": {
                        "type": "VECTOR_TILE",
                        "raster": None,
                        "vector": {
                            "tile_server": {
                                "name": "CUSTOM",
                                "custom": {
                                    "url": "https://custom-osm-data/{x}/{y}/{z}.pbf",
                                    "credits": "custom osm",
                                    "source_layer": "custom-source-name",
                                    "min_zoom": 0,
                                    "max_zoom": 14,
                                },
                                "openStreetMap": None,
                                "openFreeMap": None,
                                "versatiles": None,
                            },
                            "fill_color": "#ff00ff",
                            "fill_opacity": 1.0,
                            "line_color": "#ffff00",
                            "line_opacity": 1.0,
                            "line_width": 1.0,
                            "line_dasharray": [1, 1],
                            "circle_color": "#0000ff",
                            "circle_opacity": 1.0,
                            "circle_radius": 10.0,
                        },
                    },
                },
            ),
        ]

    def test_projects(self):
        def _query():
            return self.query_check(
                self.Query.PROJECTS,
                variables={
                    "pagination": {
                        "limit": 10,
                        "offset": 0,
                    },
                    "includeAll": True,
                },
            )

        # Without authentication -----
        content = _query()
        assert content["data"]["projects"] == {
            **self.g_pagination(offset=0, limit=10, total_count=0, results=[]),
        }, content

        # With authentication -----
        self.force_login(self.user)
        content = _query()
        assert content["data"]["projects"] == {
            **self.g_pagination(
                offset=0,
                limit=10,
                total_count=4,
                results=[
                    dict(
                        name=f"{project.project_type_enum.label} - {project.topic} - {project.region} ({project.project_number}) {project.requesting_organization.name}",  # noqa: E501
                        topic=project.topic,
                        region=project.region,
                        projectNumber=project.project_number,
                        id=self.gID(project.pk),
                        projectType=self.genum(project.project_type_enum),
                        projectTypeSpecifics=format_object_keys(project.project_type_specifics, to_camel_case),
                    )
                    for project in self.projects
                ],
            ),
        }, content

        annotated_projects = Project.objects.filter(
            pk__in=[p.pk for p in self.projects],
        ).annotate(
            gen_name=Project.generate_name_query(),
        )

        for project in annotated_projects:
            generated_name = project.generate_name()
            generated_name_from_query = project.gen_name  # type: ignore[reportAttributeAccessIssue]

            assert generated_name == generated_name_from_query, f"Name mismatch for project {project.pk}"


MAX_LIMIT = 10


@override_settings(
    STRAWBERRY_DJANGO={
        **STRAWBERRY_DJANGO,
        "PUBLIC_PAGINATION_MAX_LIMIT": MAX_LIMIT,
    },
)
class TestPublicQueriesQuery(TestCase):
    class Query:
        PUBLIC_PROJECTS = """
            query PublicProjects($pagination: OffsetPaginationInput) {
              publicProjects(order: {id: ASC}, pagination: $pagination) {
                totalCount
                pageInfo {
                  offset
                  limit
                }
                results {
                  id
                }
              }
            }
        """
        PUBLIC_ORGANIZATIONS = """
            query PublicOrganizations($pagination: OffsetPaginationInput) {
              publicOrganizations(order: {id: ASC}, pagination: $pagination) {
                totalCount
                pageInfo {
                  offset
                  limit
                }
                results {
                  id
                }
              }
            }
        """

    @typing.override
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = UserFactory.create()
        cls.user_resource_kwargs = dict(
            created_by=cls.user,
            modified_by=cls.user,
        )
        cls.active_organization = OrganizationFactory.create(**cls.user_resource_kwargs)
        cls.archived_organization = OrganizationFactory.create(
            **cls.user_resource_kwargs,
            is_archived=True,
        )
        cls.published_project = ProjectFactory.create(
            **cls.user_resource_kwargs,
            requesting_organization=cls.active_organization,
            project_type=ProjectTypeEnum.FIND,
            status=ProjectStatusEnum.PUBLISHED,
        )
        cls.paused_project = ProjectFactory.create(
            **cls.user_resource_kwargs,
            requesting_organization=cls.active_organization,
            project_type=ProjectTypeEnum.FIND,
            status=ProjectStatusEnum.PAUSED,
        )
        cls.finished_project = ProjectFactory.create(
            **cls.user_resource_kwargs,
            requesting_organization=cls.active_organization,
            project_type=ProjectTypeEnum.FIND,
            status=ProjectStatusEnum.FINISHED,
        )
        cls.draft_project = ProjectFactory.create(
            **cls.user_resource_kwargs,
            requesting_organization=cls.active_organization,
            project_type=ProjectTypeEnum.FIND,
            status=ProjectStatusEnum.DRAFT,
        )

    def test_public_projects_returns_only_public_statuses(self) -> None:
        content = self.query_check(self.Query.PUBLIC_PROJECTS, variables={"pagination": {"limit": 10, "offset": 0}})
        result = content["data"]["publicProjects"]
        returned_ids = {r["id"] for r in result["results"]}
        assert result["totalCount"] == 3
        assert self.gID(self.published_project.pk) in returned_ids
        assert self.gID(self.paused_project.pk) in returned_ids
        assert self.gID(self.finished_project.pk) in returned_ids
        assert self.gID(self.draft_project.pk) not in returned_ids

    def test_public_projects_high_limit_is_capped(self) -> None:
        for _ in range(MAX_LIMIT):
            ProjectFactory.create(
                **self.user_resource_kwargs,
                requesting_organization=self.active_organization,
                project_type=ProjectTypeEnum.FIND,
                status=ProjectStatusEnum.PUBLISHED,
            )
        content = self.query_check(
            self.Query.PUBLIC_PROJECTS,
            variables={"pagination": {"limit": MAX_LIMIT + 10, "offset": 0}},
        )
        assert len(content["data"]["publicProjects"]["results"]) == MAX_LIMIT

    def test_public_organizations_returns_only_active(self) -> None:
        content = self.query_check(self.Query.PUBLIC_ORGANIZATIONS, variables={"pagination": {"limit": 10, "offset": 0}})
        result = content["data"]["publicOrganizations"]
        returned_ids = {r["id"] for r in result["results"]}
        assert self.gID(self.active_organization.pk) in returned_ids
        assert self.gID(self.archived_organization.pk) not in returned_ids

    def test_public_organizations_high_limit_is_capped(self) -> None:
        for _ in range(MAX_LIMIT):
            OrganizationFactory.create(**self.user_resource_kwargs)
        content = self.query_check(
            self.Query.PUBLIC_ORGANIZATIONS,
            variables={"pagination": {"limit": MAX_LIMIT + 10, "offset": 0}},
        )
        assert len(content["data"]["publicOrganizations"]["results"]) == MAX_LIMIT

    def test_public_projects_no_pagination_uses_default(self) -> None:
        content = self.query_check(self.Query.PUBLIC_PROJECTS)
        result = content["data"]["publicProjects"]
        assert result["pageInfo"]["limit"] == MAX_LIMIT

    def test_public_organizations_no_pagination_uses_default(self) -> None:
        content = self.query_check(self.Query.PUBLIC_ORGANIZATIONS)
        result = content["data"]["publicOrganizations"]
        assert result["pageInfo"]["limit"] == MAX_LIMIT

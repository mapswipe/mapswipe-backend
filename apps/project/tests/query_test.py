import typing

from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.project.models import ProjectTypeEnum
from apps.user.factories import UserFactory
from main.tests import TestCase
from utils.common import format_object_keys, to_camel_case


class TestProjectQuery(TestCase):
    class Query:
        PROJECTS = """
            fragment VectorTileServerPropertyFields on ProjectVectorTileServerConfig {
                name
                custom {
                  credits
                  sourceName
                  url
                  minZoom
                  maxZoom
                }
                openFreeMap {
                  credits
                  sourceName
                }
                openStreetMap {
                  credits
                  sourceName
                }
                versatiles {
                  credits
                  sourceName
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
            query Projects($pagination: OffsetPaginationInput) {
              projects(order: {id: ASC}, pagination: $pagination) {
                totalCount
                pageInfo {
                  offset
                  limit
                }
                results {
                  id
                  name
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
                                    "url": "https://custom-osm-data",
                                    "credits": "custom osm",
                                    "source_name": "custom-source-name",
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
                        id=self.gID(project.pk),
                        name=project.name,
                        projectType=self.genum(project.project_type_enum),
                        projectTypeSpecifics=format_object_keys(project.project_type_specifics, to_camel_case),
                    )
                    for project in self.projects
                ],
            ),
        }, content

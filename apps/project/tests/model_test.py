import typing

from django.contrib.gis.geos import Polygon

from apps.project.factories import OrganizationFactory, ProjectFactory
from apps.project.models import Geometry, Project
from apps.user.factories import UserFactory
from main.tests import TestCase


class TestProjectAoiGeometry(TestCase):
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

    def create_project_with_aoi_geometry(self) -> Project:
        geometry = Geometry.objects.create(
            geometry=Polygon.from_bbox((0, 0, 1, 1)),
            total_area=1,
        )
        return ProjectFactory.create(
            **self.user_resource_kwargs,
            requesting_organization=self.organization,
            aoi_geometry=geometry,
        )

    def test_deleting_geometry_keeps_project(self):
        """A geometry is subordinate to its project, so its deletion only clears the relation."""
        project = self.create_project_with_aoi_geometry()

        typing.cast("Geometry", project.aoi_geometry).delete()

        project.refresh_from_db()
        assert project.aoi_geometry_id is None
        assert Geometry.objects.count() == 0

    def test_deleting_project_deletes_geometry(self):
        project = self.create_project_with_aoi_geometry()

        project.delete()

        assert Geometry.objects.count() == 0

    def test_deleting_project_queryset_deletes_geometry(self):
        project = self.create_project_with_aoi_geometry()

        Project.objects.filter(pk=project.pk).delete()

        assert Geometry.objects.count() == 0

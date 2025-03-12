import logging
import os
import tempfile
from abc import ABC

from django.conf import settings
from pydantic import Field

from apps.project.models import Project, ProjectTask, ProjectTaskGroup
from main.bulk_managers import BulkCreateManager
from utils.geo import tile_functions, tile_grouping
from utils.geo.tile_server.models import TileServerConfigAlias
from utils.geo.tile_server.tile_server import AvailableTileServerTypeAlias, get_tile_server

from ...base.project import BaseProject

logger = logging.getLogger(__name__)


class TileMapServiceBaseProject(BaseProject, ABC):
    class ProjectProperty(BaseProject.ProjectProperty):
        tile_server_property: TileServerConfigAlias = Field(discriminator="name")

    class ProjectTaskGroupProperty(BaseProject.ProjectTaskGroupProperty):
        x_max: int
        x_min: int
        y_max: int
        y_min: int

    class ProjectTaskProperty(BaseProject.ProjectTaskProperty):
        url: str
        tile_x: int
        tile_y: int

    tile_server: AvailableTileServerTypeAlias
    project_type_specifics: ProjectProperty

    def __init__(self, project: Project):
        self.project = project
        self.project_type_specifics = project.project_type_specifics
        self.tile_server = get_tile_server(self.project_type_specifics.tile_server_property)

    def _create_tasks(self, group: ProjectTaskGroup, raw_group: tile_grouping.RawGroup) -> int:
        bulk_mgr = BulkCreateManager(chunk_size=1000)

        tasks_count = 0
        for tile_x in range(raw_group["xMin"], raw_group["xMax"] + 1):
            for tile_y in range(raw_group["yMin"], raw_group["yMax"] + 1):
                geometry = tile_functions.geometry_from_tile_coords(tile_x, tile_y, self.project.zoom_level)
                url = self.tile_server.generate_url(tile_x, tile_y, self.project.zoom_level)
                bulk_mgr.add(
                    ProjectTask(
                        task_group_id=group.pk,
                        geometry=geometry,
                        project_type_specifics=self.ProjectTaskProperty(
                            tile_x=tile_x,
                            tile_y=tile_y,
                            url=url,
                        ),
                    )
                )
                tasks_count += 1
        bulk_mgr.done()
        return tasks_count

    def create_groups(self):
        """Create groups for project extent."""
        for _, raw_group in self.raw_groups.items():
            # Create new group
            # TODO: Bulk create here as well?
            new_group = ProjectTaskGroup.objects.create(
                project_id=self.project.pk,
                number_of_tasks=0,
                progress=0,
                finished_count=0,
                required_count=0,
                project_type_specifics=self.ProjectTaskGroupProperty(
                    x_max=raw_group["xMax"],
                    x_min=raw_group["xMin"],
                    y_max=raw_group["yMax"],
                    y_min=raw_group["yMin"],
                ),
            )
            # Create new tasks for this group
            total_tasks = self._create_tasks(new_group, raw_group)
            logger.info(f"Created {total_tasks} tasks for group: {new_group.pk}")

    def validate_geometries(self):
        """Create groups for project extent."""
        # first step get properties of each group from extent
        _, extension = os.path.splitext(self.project.geometry_file.file.name)
        with tempfile.NamedTemporaryFile(suffix=extension, dir=settings.TEMP_DIR) as temp_file:
            # FIXME: self.project.geometry is not a file
            temp_file.write(self.project.geometry_file.file.read())
            temp_file.flush()
            self.raw_groups = tile_grouping.extent_to_groups(
                temp_file.name,
                self.project.zoom_level,
                self.project.group_size,
            )

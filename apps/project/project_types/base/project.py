import logging
from abc import ABC, abstractmethod

from django.db import models
from pydantic import BaseModel

from apps.project.models import Project, ProjectTask, ProjectTaskGroup
from utils.geo import tile_grouping

logger = logging.getLogger(__name__)


class BaseProject(ABC):
    class ProjectProperty(BaseModel, ABC): ...

    class ProjectTaskGroupProperty(BaseModel, ABC): ...

    class ProjectTaskProperty(BaseModel, ABC): ...

    project: Project
    raw_groups: dict[str, tile_grouping.RawGroup]

    def __init__(self, project: Project):
        self.project = project

    def post_create_groups(self):
        # Update number_of_tasks
        ProjectTaskGroup.objects.filter(
            project_id=self.project.pk,
        ).update(
            number_of_tasks=models.Subquery(
                ProjectTask.objects.filter(id=models.OuterRef("id"))
                .annotate(total_tasks=models.Count("*"))
                .values("total_tasks")[:1]
            )
        )

        # TODO: Calculate: total_area, time_spent_max_allowed

    @abstractmethod
    def validate_geometries(self): ...

    @abstractmethod
    def _create_tasks(self, group: ProjectTaskGroup, raw_group: tile_grouping.RawGroup) -> int: ...

    @abstractmethod
    def create_groups(self): ...

    def save_project(self):
        """
        Save all project info with groups and tasks in postgres.

        Returns
        ------
            Boolean: True = Successful
        """
        logger.info(f"{self.project.pk} - start creating a project")

        self.validate_geometries()
        self.create_groups()
        self.post_create_groups()
        return True

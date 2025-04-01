import logging
import typing
from abc import ABC, abstractmethod

from django.db import models
from pydantic import BaseModel

from apps.project.models import Project, ProjectTask, ProjectTaskGroup
from utils.geo import tile_grouping

logger = logging.getLogger(__name__)


class BaseProjectProperty(BaseModel, ABC): ...


class BaseProjectTaskGroupProperty(BaseModel, ABC): ...


class BaseProjectTaskProperty(BaseModel, ABC): ...


ProjectPropertyTypeVar = typing.TypeVar("ProjectPropertyTypeVar", bound=BaseProjectProperty)
ProjectTaskGroupPropertyTypeVar = typing.TypeVar("ProjectTaskGroupPropertyTypeVar", bound=BaseProjectTaskGroupProperty)
ProjectTaskPropertyTypeVar = typing.TypeVar("ProjectTaskPropertyTypeVar", bound=BaseProjectTaskProperty)


class BaseProject(
    ABC,
    typing.Generic[
        ProjectPropertyTypeVar,
        ProjectTaskGroupPropertyTypeVar,
        ProjectTaskPropertyTypeVar,
    ],
):
    project_property_class: typing.Type[ProjectPropertyTypeVar]
    project_task_group_property_class: typing.Type[ProjectTaskGroupPropertyTypeVar]
    project_task_property_class: typing.Type[ProjectTaskPropertyTypeVar]

    raw_groups: dict[str, tile_grouping.RawGroup]

    def __init__(self, project: Project):
        self.project = project
        self.project_type_specifics = self.project_property_class(**project.project_type_specifics)

    @classmethod
    def _inheritance_checks(cls):
        # TODO: Find a better way to skip for base classes
        if cls.__name__.endswith("BaseProject"):
            # Skip check for the abstract class
            return

        missing_fields = []
        for attr_name in [
            "project_property_class",
            "project_task_group_property_class",
            "project_task_property_class",
        ]:
            if getattr(cls, attr_name, None) is None:
                missing_fields.append(attr_name)

        if missing_fields:
            raise NotImplementedError(f"Please define {','.join(missing_fields)} for {cls}")

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._inheritance_checks()

    def post_create_groups(self):
        # Update number_of_tasks
        ProjectTaskGroup.objects.filter(
            project_id=self.project.pk,
        ).update(
            number_of_tasks=models.Subquery(
                ProjectTask.objects.filter(task_group_id=models.OuterRef("id"))
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

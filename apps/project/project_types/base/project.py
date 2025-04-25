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


class ValidateException(Exception): ...


ProjectPropertyTypeVar = typing.TypeVar("ProjectPropertyTypeVar", bound=BaseProjectProperty)
ProjectTaskGroupPropertyTypeVar = typing.TypeVar("ProjectTaskGroupPropertyTypeVar", bound=BaseProjectTaskGroupProperty)
ProjectTaskPropertyTypeVar = typing.TypeVar("ProjectTaskPropertyTypeVar", bound=BaseProjectTaskProperty)

ValidateResponse = typing.TypeVar("ValidateResponse")


class BaseProject(
    ABC,
    typing.Generic[
        ProjectPropertyTypeVar,
        ProjectTaskGroupPropertyTypeVar,
        ProjectTaskPropertyTypeVar,
        ValidateResponse,
    ],
):
    project_property_class: type[ProjectPropertyTypeVar]
    project_task_group_property_class: type[ProjectTaskGroupPropertyTypeVar]
    project_task_property_class: type[ProjectTaskPropertyTypeVar]

    def __init__(self, project: Project):
        self.project = project
        self.project_type_specifics = self.project_property_class(**project.project_type_specifics)

    @classmethod
    def _inheritance_checks(cls):
        # TODO(thenav56): Find a better way to skip for base classes
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

    def analyze_groups(self):
        # Update number_of_tasks
        self.project.update_processing_status(Project.ProcessingStatus.ANALYZING_GROUPS_AND_TASK, True)

        ProjectTaskGroup.objects.filter(
            project_id=self.project.pk,
        ).update(
            number_of_tasks=models.Subquery(
                ProjectTask.objects.filter(task_group_id=models.OuterRef("id"))
                .values("task_group_id")
                .annotate(total_tasks=models.Count("*"))
                .values("total_tasks")[:1],
            ),
        )

    @abstractmethod
    def post_create_groups(self): ...

    @abstractmethod
    def validate(self) -> ValidateResponse: ...

    # FIXME(tnagorra): This is not generic enough
    @abstractmethod
    def _create_tasks(self, group: ProjectTaskGroup, raw_group: tile_grouping.RawGroup) -> int: ...

    @abstractmethod
    def create_groups(self, resp: ValidateResponse): ...

    def process_project(self) -> bool:
        """
        Save all project info with groups and tasks in postgres.
        """

        if self.project.status not in [
            Project.Status.MARKED_AS_READY,
            Project.Status.FAILED,
        ]:
            raise Exception("Project can only be processed if is either 'Marked as ready' or 'Failed'")

        logger.info("%s - start creating a project", self.project.pk)

        self.project.update_processing_status(Project.ProcessingStatus.PREPARING, True)
        # TODO(tnagorra): We need to cleanup groups, tasks and files
        # for failed items

        try:
            # TODO(tnagorra): Handle updates to processstatus
            resp = self.validate()
            self.create_groups(resp)
            self.analyze_groups()
            self.post_create_groups()

            self.project.update_processing_status(Project.ProcessingStatus.COMPLETED, True)
            self.project.update_status(Project.Status.READY, True)
            return True
        except ValidateException as ex:
            logger.error(ex)
            self.project.update_status(Project.Status.FAILED, True)
            return False

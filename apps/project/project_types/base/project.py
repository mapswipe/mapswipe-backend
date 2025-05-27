import logging
from abc import ABC, abstractmethod

from django.contrib.gis.db.models.functions import Area
from django.db import models
from pydantic import BaseModel

from apps.project.models import Project, ProjectAsset, ProjectTask, ProjectTaskGroup, ProjectTypeEnum
from utils.geo import tile_grouping

logger = logging.getLogger(__name__)


def get_max_time_spend_percentile(project_type: ProjectTypeEnum) -> float:
    """
    Factor calculated by @Hagellach37
    For defining the threshold for outliers using `95_percent`

    |project_type|median|95_percent|avg|
    |------------|------|----------|---|
    |1|00:00:00.208768|00:00:01.398161|00:00:28.951521|
    |2|00:00:01.330297|00:00:06.076814|00:00:03.481192|
    |3|00:00:02.092967|00:00:11.271081|00:00:06.045881|
    """
    match project_type:
        case ProjectTypeEnum.FIND:
            return 1.4
        case ProjectTypeEnum.COMPLETENESS:
            return 1.4
        case ProjectTypeEnum.COMPARE:
            return 11.2
        case ProjectTypeEnum.VALIDATE:
            return 6.1
        # case ProjectTypeEnum.STREET:
        #     return 65


class BaseProjectProperty(BaseModel, ABC): ...


class BaseProjectTaskGroupProperty(BaseModel, ABC): ...


class BaseProjectTaskProperty(BaseModel, ABC): ...


class ValidateException(Exception): ...


class BaseProject[
    ProjectPropertyTypeVar: BaseProjectProperty,
    ProjectTaskGroupPropertyTypeVar: BaseProjectTaskGroupProperty,
    ProjectTaskPropertyTypeVar: BaseProjectTaskProperty,
    ValidateResponse,
](ABC):
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

        project_task_groups_qs = ProjectTaskGroup.objects.filter(project_id=self.project.pk)

        project_task_groups_qs.update(
            number_of_tasks=models.Subquery(
                ProjectTask.objects.filter(task_group_id=models.OuterRef("id"))
                .values("task_group_id")
                .annotate(total_tasks=models.Count("*"))
                .values("total_tasks")[:1],
            ),
            total_area=models.Subquery(
                ProjectTask.objects.filter(task_group_id=models.OuterRef("id"))
                .values("task_group_id")
                .annotate(total_task_group_area=models.Sum(Area("geometry")))
                .values("total_task_group_area")[:1],
            ),
        )

        # NOTE: After number_of_tasks is calculated
        project_task_groups_qs.update(
            time_spent_max_allowed=(
                models.F("number_of_tasks") * get_max_time_spend_percentile(self.project.project_type_enum)
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
        ProjectTaskGroup.objects.filter(project=self.project.pk).delete()
        # TODO(tnagorra): We need to add a CRON to delete these project assets
        # FIXME(tnagorra): Do we also cleanup the user INPUT?
        # We need to be careful not to delete assets that are currently used
        ProjectAsset.usable_objects().filter(
            project=self.project.pk,
            type__in=[ProjectAsset.Type.OUTPUT, ProjectAsset.Type.STATS],
        ).update(marked_as_deleted=True)

        try:
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

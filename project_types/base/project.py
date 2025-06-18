import logging
import typing
from abc import ABC, abstractmethod

from django.contrib.gis.db.models.functions import Area
from django.db import models
from django.utils import timezone
from firebase_admin.db import Reference as FbReference
from pydantic import BaseModel

from apps.project.models import FirebasePushStatusEnum, Project, ProjectAsset, ProjectTask, ProjectTaskGroup, ProjectTypeEnum
from main.config import Config
from main.logging import log_extra
from utils.firebase import FbProject

logger = logging.getLogger(__name__)


# FIXME(tnagorra): We should define these in each project type class
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
        case ProjectTypeEnum.VALIDATE_IMAGE:
            return 6.1
        # case ProjectTypeEnum.STREET:
        #     return 65


class BaseProjectProperty(BaseModel, ABC): ...


class BaseProjectTaskGroupProperty(BaseModel, ABC): ...


class BaseProjectTaskProperty(BaseModel, ABC): ...


class ValidationException(Exception): ...


class BaseProject[
    ProjectPropertyTypeVar: BaseProjectProperty,
    ProjectTaskGroupPropertyTypeVar: BaseProjectTaskGroupProperty,
    ProjectTaskPropertyTypeVar: BaseProjectTaskProperty,
    ValidatedData,
    AdditionalGroupData,
](ABC):
    project_property_class: type[ProjectPropertyTypeVar]
    project_task_group_property_class: type[ProjectTaskGroupPropertyTypeVar]
    project_task_property_class: type[ProjectTaskPropertyTypeVar]

    def __init__(self, project: Project):
        self.project = project
        self.project_type_specifics = self.project_property_class(**project.project_type_specifics)

        self.firebase_helper = Config.FIREBASE_HELPER

    @classmethod
    def _inheritance_checks(cls):
        # FIXME(thenav56): Find a better way to skip for base classes
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
    def validate(self) -> ValidatedData: ...

    @abstractmethod
    def create_tasks(self, group: ProjectTaskGroup, raw_group: AdditionalGroupData) -> int: ...

    @abstractmethod
    def create_groups(self, resp: ValidatedData): ...

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
        except ValidationException as ex:
            logger.error(ex)
            self.project.update_status(Project.Status.FAILED, True)
            return False

    @abstractmethod
    def handle_new_project_on_firebase(self, project_ref: FbReference): ...

    # TODO(tnagorra): Get type of fb_project from pydantic
    @abstractmethod
    def handle_project_update_on_firebase(self, project_ref: FbReference, fb_project: FbProject): ...

    def push_to_firebase(self):
        if self.project.firebase_push_status_enum != FirebasePushStatusEnum.PENDING:
            logger.warning("%s - push_to_firebase called when push is not required", self.project.pk)
            return

        self.project.update_firebase_push_status(FirebasePushStatusEnum.PROCESSING)

        try:
            project_ref = self.firebase_helper.ref(
                Config.FirebaseKeys.project(self.project.id),
            )
            # TODO(tnagorra): Use pydantic class
            # TODO(tnagorra): We need to make this type more specific on project specific handlers
            fb_project: typing.Any = project_ref.get()

            if not self.project.firebase_last_pushed:
                if fb_project is not None:
                    logger.error(
                        "push_to_firebase found a project already in firebase when creating a project",
                        extra=log_extra({"project": self.project.pk}),
                    )
                    raise Exception
                self.handle_new_project_on_firebase(project_ref)
            else:
                if fb_project is None:
                    logger.error(
                        "push_to_firebase found did not find project in firebase when updating a project",
                        extra=log_extra({"project": self.project.pk}),
                    )
                    raise Exception
                valid_project = FbProject.model_validate(obj=fb_project)
                self.handle_project_update_on_firebase(project_ref, valid_project)
        except Exception as ex:
            self.project.update_firebase_push_status(FirebasePushStatusEnum.FAILED)
            raise ex from ex
        else:
            self.project.firebase_last_pushed = timezone.now()
            self.project.update_firebase_push_status(FirebasePushStatusEnum.SUCCESS, commit=False)
            self.project.save(
                update_fields=[
                    "firebase_last_pushed",
                    "firebase_push_status",
                ],
            )

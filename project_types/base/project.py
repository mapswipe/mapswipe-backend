import json
import logging
import typing
from abc import ABC, abstractmethod
from collections import defaultdict

from django.contrib.gis.db.models.functions import Area
from django.core.files.base import ContentFile
from django.db import models
from firebase_admin.db import Reference as FbReference
from pydantic import BaseModel, ConfigDict
from pyfirebase_mapswipe import extended_models as firebase_ext_models
from pyfirebase_mapswipe import models as firebase_models
from pyfirebase_mapswipe import utils as firebase_utils

from apps.common.models import FirebasePushStatusEnum
from apps.project.models import (
    Project,
    ProjectAsset,
    ProjectStatusEnum,
    ProjectTask,
    ProjectTaskGroup,
    ProjectTypeEnum,
)
from main.config import Config
from main.logging import log_extra
from project_types.firebase import project_type_enum_to_firebase
from utils.common import compress_tasks

logger = logging.getLogger(__name__)


class InvalidProjectPushException(Exception): ...


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
            # FIXME(tnagorra): We need to update this value once the feature is deployed
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
            required_count=models.F("number_of_tasks") * self.project.verification_number,
            time_spent_max_allowed=(
                models.F("number_of_tasks") * get_max_time_spend_percentile(self.project.project_type_enum)
            ),
        )

        self.project.required_results = (
            ProjectTaskGroup.objects.filter(project_id=self.project.pk)
            .values("project_id")
            .annotate(required_results=models.Sum("required_count"))
            .values("required_results")[:1]
        )
        self.project.save(update_fields=(["required_results"]))

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
        # FIXME(tnagorra): Do we also clean up the user INPUT?
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

    def _generate_and_save_task_file(self, grouped_tasks: dict[int, list[dict[str, typing.Any]]]) -> None:
        """
        Generates a JSON file with all tasks and save it as a project asset.
        Using this for debugging purpose of zipped tasks file.
        """
        task_json = json.dumps(grouped_tasks, separators=(",", ":"))
        filename = f"project_grouped_tasks_{self.project.id}.json"
        content_file = ContentFile(
            task_json.encode("utf-8"),
            filename,
        )
        ProjectAsset.objects.create(
            project=self.project,
            file=content_file,
            file_size=content_file.size,
            mimetype=ProjectAsset.Mimetype.JSON,
            type=ProjectAsset.Type.DEBUG,
            # FIXME: Maybe create a internal user like mapswipe-bot
            created_by=self.project.modified_by,
            modified_by=self.project.modified_by,
        )

    def handle_new_tasks_on_firebase(self, task_ref: FbReference):
        tasks = ProjectTask.objects.filter(task_group__project_id=self.project.pk)
        grouped_tasks: dict[int, list[dict[str, typing.Any]]] = defaultdict(list)

        for task in tasks.iterator():
            task_data = firebase_models.FbMappingTaskCreateOnlyInput(
                projectId=self.project.firebase_id,
            )
            task_project_specific_data = self.get_task_project_specifics_for_firebase(task)
            serialized_task = {
                **firebase_utils.serialize(task_data),
                **firebase_utils.serialize(task_project_specific_data),
            }

            grouped_tasks[task.task_group_id].append(serialized_task)

        grouped_tasks_dict: dict[int, typing.Any] = dict(grouped_tasks)

        # NOTE: We are using compression to reduce the size of the data sent to Firebase
        if self.enable_compression_for_tasks():
            # NOTE: Saving the raw file for debugging purpose
            self._generate_and_save_task_file(grouped_tasks)

            grouped_tasks_dict = {
                group_id: compress_tasks(tasks_list) for group_id, tasks_list in grouped_tasks_dict.items()
            }

        # Use Bulk Manager
        task_ref.set(value=grouped_tasks_dict)

    def handle_new_groups_on_firebase(self, group_ref: FbReference):
        groups = ProjectTaskGroup.objects.filter(project_id=self.project.pk)
        fb_groups: dict[str, dict[str, dict]] = {}
        for group in groups.iterator():
            group_data = firebase_ext_models.FbMappingGroup(
                finishedCount=0,
                progress=0,
                projectId=self.project.firebase_id,
                numberOfTasks=group.number_of_tasks,
                requiredCount=group.required_count,
            )
            group_project_specific_data = self.get_group_project_specifics_for_firebase(group)
            fb_groups[group.pk] = {
                **firebase_utils.serialize(group_data),
                **firebase_utils.serialize(group_project_specific_data),
            }

        # FIXME(tnagorra): Use bulk uploader
        group_ref.set(value=fb_groups)

    @abstractmethod
    def get_task_project_specifics_for_firebase(self, task: ProjectTask) -> BaseModel: ...

    @abstractmethod
    def get_group_project_specifics_for_firebase(self, group: ProjectTaskGroup) -> BaseModel: ...

    @abstractmethod
    def get_project_specifics_for_firebase(self) -> BaseModel: ...

    def skip_tasks_for_firebase(self) -> bool:
        return False

    def enable_compression_for_tasks(self) -> bool:
        return False

    def handle_new_project_on_firebase(self, project_ref: FbReference):
        assert self.project.tutorial_id is not None, "Tutorial is required before project can be pushed to firebase"
        assert self.project.tutorial is not None, "Tutorial is required before project can be pushed to firebase"

        # NOTE: We are not reading data from group_ref as it's an expensive operation
        # FIXME(tnagorra): We need to check if the key exists later
        group_ref = self.firebase_helper.ref(
            Config.FirebaseKeys.project_groups(self.project.firebase_id),
        )
        # FIXME(tnagorra): We need to check if the key exists later
        task_ref = self.firebase_helper.ref(
            Config.FirebaseKeys.project_tasks(self.project.firebase_id),
        )

        # FIXME: If taskId is defined, should be private_inactive
        status = firebase_models.FbEnumProjectStatus.INACTIVE
        if self.project.status_enum == ProjectStatusEnum.PUBLISHED:
            # FIXME: If taskId is defined, should be private_active
            status = firebase_models.FbEnumProjectStatus.PRIVATE_ACTIVE

        if not self.skip_tasks_for_firebase():
            self.handle_new_tasks_on_firebase(task_ref)
        self.handle_new_groups_on_firebase(group_ref)

        project_data = firebase_ext_models.FbProject(
            created=self.project.created_at,
            # FIXME: use firebase_id later
            createdBy=self.project.created_by.old_id or str(self.project.created_by_id),
            image=self.project.image.file.url if self.project.image else None,
            isFeatured=self.project.is_featured,
            lookFor=self.project.look_for,
            manualUrl=self.project.additional_info_url,
            maxTasksPerUser=self.project.max_tasks_per_user,
            groupMaxSize=self.project.group_size,  # this is zero
            contributorCount=0,
            progress=0,
            resultCount=0,
            groupSize=self.project.group_size,
            projectId=self.project.firebase_id,
            name=self.project.generate_name(),
            projectDetails=self.project.description or "n/a",
            projectNumber=self.project.project_number,
            projectRegion=self.project.region,
            projectTopic=self.project.topic,
            projectTopicKey=self.project.generate_name().lower().strip(),
            projectType=project_type_enum_to_firebase(self.project.project_type_enum),
            # project_type=project_type_enum_to_firebase(self.project.project_type_enum), # not needed here
            requestingOrganisation=self.project.requesting_organization.name,  # str
            requiredResults=self.project.required_results,
            status=status,
            teamId=self.project.team.firebase_id if self.project.team else None,
            # FIXME(tnagorra): Need to check how we get this?
            language="en-us",
            tutorialId=self.project.tutorial.firebase_id,
            verificationNumber=self.project.verification_number,
        )

        project_specific_data = self.get_project_specifics_for_firebase()

        project_ref.set(
            value={
                **firebase_utils.serialize(project_data),
                **firebase_utils.serialize(project_specific_data),
            },
        )

    def handle_project_update_on_firebase(self, project_ref: FbReference, fb_project: firebase_ext_models.FbProject):
        assert self.project.tutorial_id is not None, "Tutorial is required before project can be pushed to firebase"

        status = fb_project.status
        if (
            status
            in [
                firebase_models.FbEnumProjectStatus.INACTIVE,
                firebase_models.FbEnumProjectStatus.PRIVATE_INACTIVE,
            ]
            and self.project.status_enum == ProjectStatusEnum.PUBLISHED
        ):
            # FIXME: If taskId is defined, should be private_active
            status = firebase_models.FbEnumProjectStatus.ACTIVE
        elif status in [
            firebase_models.FbEnumProjectStatus.ACTIVE,
            firebase_models.FbEnumProjectStatus.PRIVATE_ACTIVE,
        ] and self.project.status_enum in [ProjectStatusEnum.ARCHIVED, ProjectStatusEnum.PAUSED]:
            # FIXME: If taskId is defined, should be private_inactive
            status = firebase_models.FbEnumProjectStatus.INACTIVE

        project_ref.update(
            value=firebase_utils.serialize(
                firebase_models.FbProjectUpdateInput(
                    image=self.project.image.file.url if self.project.image else None,
                    isFeatured=self.project.is_featured,
                    lookFor=self.project.look_for,
                    name=self.project.generate_name(),
                    projectNumber=self.project.project_number,
                    projectRegion=self.project.region,
                    projectTopic=self.project.topic,
                    projectTopicKey=self.project.generate_name().lower().strip(),
                    projectDetails=self.project.description or "n/a",
                    requestingOrganisation=self.project.requesting_organization.name,
                    tutorialId=self.project.tutorial.firebase_id,
                    status=status,
                    teamId=self.project.team.firebase_id if self.project.team else None,
                    # FIXME(tnagorra): Need to check how we get this?
                    language="en-us",
                ),
            ),
        )

    def push_to_firebase(self):
        if self.project.firebase_push_status_enum != FirebasePushStatusEnum.PENDING:
            logger.warning("%s - push_to_firebase called when push is not required", self.project.pk)
            return

        self.project.update_firebase_push_status(FirebasePushStatusEnum.PROCESSING)

        try:
            project_ref = self.firebase_helper.ref(
                Config.FirebaseKeys.project(self.project.firebase_id),
            )
            fb_project: typing.Any = project_ref.get()

            if not self.project.firebase_last_pushed:
                if fb_project is not None:
                    logger.error(
                        "push_to_firebase found a project already in firebase when creating a project",
                        extra=log_extra({"project": self.project.pk}),
                    )
                    raise InvalidProjectPushException
                self.handle_new_project_on_firebase(project_ref)
            else:
                if fb_project is None:
                    logger.error(
                        "push_to_firebase did not find project in firebase when updating a project",
                        extra=log_extra({"project": self.project.pk}),
                    )
                    raise InvalidProjectPushException

                class RelaxedModel(firebase_ext_models.FbProject):
                    model_config = ConfigDict(extra="ignore")

                # NOTE: we want to ignore extra fields from firebase
                valid_project = RelaxedModel.model_validate(obj=fb_project)
                valid_project = firebase_ext_models.FbProject.model_validate(obj=valid_project)

                self.handle_project_update_on_firebase(project_ref, valid_project)
        except InvalidProjectPushException:
            self.project.update_firebase_push_status(FirebasePushStatusEnum.FAILED)
        except Exception:
            logger.error(
                "push_to_firebase failed",
                extra=log_extra({"project": self.project.pk}),
                exc_info=True,
            )
            self.project.update_firebase_push_status(FirebasePushStatusEnum.FAILED)
        else:
            self.project.update_firebase_push_status(FirebasePushStatusEnum.SUCCESS)

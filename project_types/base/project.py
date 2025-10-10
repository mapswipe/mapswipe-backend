import json
import logging
import typing
from abc import ABC, abstractmethod
from collections import defaultdict

from celery.exceptions import SoftTimeLimitExceeded
from django.contrib.gis.db.models import GeometryField
from django.contrib.gis.db.models.functions import Area
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.functions import Cast
from firebase_admin.db import Reference as FbReference  # type: ignore[reportMissingTypeStubs]
from pydantic import BaseModel, ConfigDict
from pyfirebase_mapswipe import extended_models as firebase_ext_models
from pyfirebase_mapswipe import models as firebase_models
from pyfirebase_mapswipe import utils as firebase_utils
from ulid import ULID

from apps.common.models import FirebasePushStatusEnum
from apps.common.utils import get_absolute_uri
from apps.project.models import (
    Project,
    ProjectAsset,
    ProjectStatusEnum,
    ProjectTask,
    ProjectTaskGroup,
)
from main.bulk_managers import FirebaseBulkManager
from main.config import Config
from main.logging import log_extra
from utils.common import compress_tasks

logger = logging.getLogger(__name__)


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
        self.project_type_specifics = self.project_property_class.model_validate(project.project_type_specifics)

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

    def __init_subclass__(cls, **kwargs):  # type: ignore[reportMissingParameterType]
        super().__init_subclass__(**kwargs)
        cls._inheritance_checks()

    @staticmethod
    def get_firebase_status(status: ProjectStatusEnum, no_team: bool):
        match status:
            case ProjectStatusEnum.FINISHED:
                return (
                    firebase_models.FbEnumProjectStatus.FINISHED
                    if no_team
                    else firebase_models.FbEnumProjectStatus.PRIVATE_FINISHED
                )
            case ProjectStatusEnum.READY_TO_PUBLISH | ProjectStatusEnum.PUBLISHED:
                return (
                    firebase_models.FbEnumProjectStatus.ACTIVE
                    if no_team
                    else firebase_models.FbEnumProjectStatus.PRIVATE_ACTIVE
                )
            case _:
                return (
                    firebase_models.FbEnumProjectStatus.INACTIVE
                    if no_team
                    else firebase_models.FbEnumProjectStatus.PRIVATE_INACTIVE
                )

    def get_aoi_geometry_asset(self) -> ProjectAsset | None:
        return None

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
                .annotate(
                    total_task_group_area=models.Sum(
                        Area(
                            Cast(
                                "geometry",
                                output_field=GeometryField(geography=True),
                            ),
                        ),
                    )
                    / 100_000,
                )
                .values("total_task_group_area")[:1],
            ),
        )
        # NOTE: After number_of_tasks is calculated
        project_task_groups_qs.update(
            required_count=self.project.verification_number,
            time_spent_max_allowed=(models.F("number_of_tasks") * self.get_max_time_spend_percentile()),
        )

        self.project.required_results = (
            ProjectTaskGroup.objects.filter(project_id=self.project.pk).aggregate(
                required_results=models.Sum("number_of_tasks") * self.project.verification_number,
            )
        )["required_results"] or 0

        if self.project.required_results == 0:
            raise ValidationException("Project does not contain any groups or tasks")

        self.project.total_area = (
            ProjectTaskGroup.objects.filter(project_id=self.project.pk).aggregate(agg_area=models.Sum("total_area"))
        )["agg_area"] or 0

        self.project.save(update_fields=(["required_results"]))

    @abstractmethod
    def get_max_time_spend_percentile(self) -> float:
        """Factor calculated by @Hagellach37
        For defining the threshold for outliers using `95_percent`.

        |project_type|median|95_percent|avg|
        |------------|------|----------|---|
        |1|00:00:00.208768|00:00:01.398161|00:00:28.951521|
        |2|00:00:01.330297|00:00:06.076814|00:00:03.481192|
        |3|00:00:02.092967|00:00:11.271081|00:00:06.045881|
        """
        ...

    def prepare(self):
        self.project.update_processing_status(Project.ProcessingStatus.PREPARING, True)

        # Cleanup tasks and groups
        ProjectTaskGroup.objects.filter(project=self.project.pk).delete()

        # Cleanup assets
        # FIXME(tnagorra): We need to add a CRON to delete these project assets
        # FIXME(tnagorra): Do we also clean up the user INPUT?
        # We need to be careful not to delete assets that are currently used
        ProjectAsset.usable_objects().filter(
            project=self.project.pk,
            type__in=[ProjectAsset.Type.OUTPUT, ProjectAsset.Type.EXPORT, ProjectAsset.Type.DEBUG],
        ).update(marked_as_deleted=True)

    @abstractmethod
    def post_create_groups(self): ...

    @abstractmethod
    def validate(self) -> ValidatedData: ...

    @abstractmethod
    def create_tasks(self, group: ProjectTaskGroup, raw_group: AdditionalGroupData) -> int: ...

    @abstractmethod
    def create_groups(self, resp: ValidatedData): ...

    def _process_project(self):
        if self.project.status_enum != Project.Status.READY_TO_PROCESS:
            raise ValidationException(
                f"Project cannot be processed if project status is '{self.project.status_enum.label}'",
            )

        logger.info("project:%s - start creating a project", self.project.pk)

        self.prepare()
        resp = self.validate()
        self.create_groups(resp)
        self.analyze_groups()
        self.post_create_groups()

    def process_project(self):
        try:
            self._process_project()
        except Exception as ex:
            if isinstance(ex, ValidationException):
                logger.warning(
                    "process_project failed",
                    extra=log_extra({"project": self.project.pk}),
                    exc_info=True,
                )
                self.project.status_message = str(ex)
            elif isinstance(ex, SoftTimeLimitExceeded):
                logger.error(
                    "process_project failed due to SoftTimeLimitExceeded",
                    extra=log_extra({"project": self.project.pk}),
                    exc_info=True,
                )
                self.project.status_message = "Project processing timed out before completion"
            else:
                logger.error(
                    "process_project failed",
                    extra=log_extra({"project": self.project.pk}),
                    exc_info=True,
                )
                self.project.status_message = (
                    "Something unexpected happened! Please reach out on the MapSwipe slack for any further assistance."
                )

            if self.project.status_enum == Project.Status.READY_TO_PROCESS:
                self.project.update_status(Project.Status.PROCESSING_FAILED, False)
            self.project.save(
                update_fields=[
                    "status",
                    "status_message",
                ],
            )
        else:
            self.project.status_message = None
            if self.project.status_enum == Project.Status.READY_TO_PROCESS:
                self.project.update_status(Project.Status.PROCESSED, False)
            self.project.update_processing_status(Project.ProcessingStatus.COMPLETED, False)
            self.project.save(
                update_fields=[
                    "status",
                    "status_message",
                    "processing_status",
                ],
            )

    # FIREBASE

    @abstractmethod
    def get_task_specifics_for_firebase(self, task: ProjectTask) -> BaseModel: ...

    @abstractmethod
    def get_group_specifics_for_firebase(self, group: ProjectTaskGroup) -> BaseModel: ...

    @abstractmethod
    def get_project_specifics_for_firebase(self) -> BaseModel: ...

    def _save_tasks_as_json(self, grouped_tasks: dict[str, list[dict[str, typing.Any]]]) -> None:
        """Generates a JSON file with all tasks and save it as a project asset.
        Using this for debugging purpose of compressed tasks.
        """
        task_json = json.dumps(grouped_tasks, separators=(",", ":"))
        filename = f"project_grouped_tasks_{self.project.pk}.json"
        content_file = ContentFile(
            task_json.encode("utf-8"),
            filename,
        )
        ProjectAsset.objects.create(
            client_id=str(ULID()),
            project=self.project,
            file=content_file,
            file_size=content_file.size,
            mimetype=ProjectAsset.Mimetype.JSON,
            type=ProjectAsset.Type.DEBUG,
            # FIXME: Maybe create a internal user like mapswipe-bot
            created_by=self.project.modified_by,
            modified_by=self.project.modified_by,
        )

    def skip_tasks_on_firebase(self) -> bool:
        return False

    def compress_tasks_on_firebase(self) -> bool:
        return False

    def create_tasks_on_firebase(self, task_ref: FbReference):
        tasks = ProjectTask.objects.filter(task_group__project_id=self.project.pk).order_by("id")
        grouped_tasks: dict[str, list[dict[str, typing.Any]]] = defaultdict(list)

        for task in tasks.iterator():
            task_data = firebase_models.FbMappingTaskCreateOnlyInput(
                projectId=self.project.firebase_id,
            )
            task_project_specific_data = self.get_task_specifics_for_firebase(task)
            serialized_task = {
                **firebase_utils.serialize(task_data),
                **firebase_utils.serialize(task_project_specific_data),
            }

            grouped_tasks[task.task_group.firebase_id].append(serialized_task)

        grouped_tasks_dict: dict[str, typing.Any] = grouped_tasks

        if self.compress_tasks_on_firebase():
            self._save_tasks_as_json(grouped_tasks)
            grouped_tasks_dict = {
                group_key: compress_tasks(tasks_list) for group_key, tasks_list in grouped_tasks_dict.items()
            }

        firebase_bulk_mgr = FirebaseBulkManager(ref=task_ref)
        for group_key, task in grouped_tasks_dict.items():
            firebase_bulk_mgr.add(
                key=group_key,
                value=task,
            )
        firebase_bulk_mgr.done()

    def create_groups_on_firebase(self, group_ref: FbReference):
        groups = ProjectTaskGroup.objects.filter(project_id=self.project.pk).order_by("id")
        fb_groups: dict[str, dict[str, dict]] = {}  # type: ignore[reportMissingTypeArgument]

        firebase_bulk_mgr = FirebaseBulkManager(ref=group_ref)

        for group in groups.iterator():
            group_data = firebase_ext_models.FbMappingGroup(
                finishedCount=0,
                progress=0,
                projectId=self.project.firebase_id,
                numberOfTasks=group.number_of_tasks,
                # FIXME(tnagorra): need to confirm if group.required_count is calculated correctly
                # requiredCount=group.required_count,
                requiredCount=self.project.verification_number,
            )
            group_project_specific_data = self.get_group_specifics_for_firebase(group)
            fb_groups[group.firebase_id] = {
                **firebase_utils.serialize(group_data),
                **firebase_utils.serialize(group_project_specific_data),
            }
            firebase_bulk_mgr.add(
                key=group.firebase_id,
                value=fb_groups[group.firebase_id],
            )

        firebase_bulk_mgr.done()

    def create_project_on_firebase(self, project_ref: FbReference):
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

        if not self.skip_tasks_on_firebase():
            self.create_tasks_on_firebase(task_ref)
        self.create_groups_on_firebase(group_ref)

        project_data = firebase_ext_models.FbProject(
            created=self.project.created_at,
            # FIXME: What to use for fallback?
            createdBy=self.project.created_by.firebase_id or str(self.project.created_by_id),
            image=get_absolute_uri(self.project.image.file if self.project.image else None),
            isFeatured=self.project.is_featured,
            lookFor=self.project.look_for,
            projectInstruction=self.project.project_instruction,
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
            projectType=self.project.project_type_enum.to_firebase(),
            # project_type=self.project.project_type_enum.to_firebase(), # not needed here
            requestingOrganisation=self.project.requesting_organization.name,
            requiredResults=self.project.required_results,
            status=BaseProject.get_firebase_status(self.project.status_enum, not self.project.team_id),
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

    def update_project_on_firebase(self, project_ref: FbReference, fb_project: firebase_ext_models.FbProject):
        assert self.project.tutorial_id is not None, "Tutorial is required before project can be pushed to firebase"
        assert self.project.tutorial is not None, "Tutorial is required before project can be pushed to firebase"

        project_ref.update(
            value=firebase_utils.serialize(
                firebase_models.FbProjectUpdateInput(
                    image=get_absolute_uri(self.project.image.file if self.project.image else None),
                    isFeatured=self.project.is_featured,
                    lookFor=self.project.look_for,
                    projectInstruction=self.project.project_instruction,
                    name=self.project.generate_name(),
                    projectNumber=self.project.project_number,
                    projectRegion=self.project.region,
                    projectTopic=self.project.topic,
                    maxTasksPerUser=self.project.max_tasks_per_user,
                    projectTopicKey=self.project.generate_name().lower().strip(),
                    projectDetails=self.project.description or "n/a",
                    requestingOrganisation=self.project.requesting_organization.name,
                    tutorialId=self.project.tutorial.firebase_id,
                    status=BaseProject.get_firebase_status(self.project.status_enum, not self.project.team_id),
                    teamId=self.project.team.firebase_id if self.project.team else None,
                    contributorCount=self.project.number_of_contributor_users,
                    progress=self.project.progress,
                    # FIXME(tnagorra): Need to check how we get this?
                    language="en-us",
                ),
            ),
        )

    def _push_project_on_firebase(self):
        if self.project.status_enum not in [
            Project.Status.READY_TO_PUBLISH,
            Project.Status.PUBLISHED,
            Project.Status.WITHDRAWN,
            Project.Status.PAUSED,
            Project.Status.FINISHED,
        ]:
            raise ValidationException(
                f"Project cannot be pushed to firebase if project status is '{self.project.status_enum.label}'",
            )
        if self.project.firebase_push_status_enum != FirebasePushStatusEnum.PENDING:
            label = self.project.firebase_push_status_enum.label if self.project.firebase_push_status_enum else "None"
            raise ValidationException(
                f"Project cannot be pushed to firebase if firebase push status is '{label}'",
            )

        self.project.update_firebase_push_status(FirebasePushStatusEnum.PROCESSING)

        project_ref = self.firebase_helper.ref(
            Config.FirebaseKeys.project(self.project.firebase_id),
        )
        fb_project: typing.Any = project_ref.get()

        if not self.project.firebase_last_pushed:
            if fb_project is not None:
                raise ValidationException(
                    "Project already found in firebase when creating a project",
                )
            self.create_project_on_firebase(project_ref)
        else:
            if fb_project is None:
                raise ValidationException(
                    "Did not find project in firebase when updating a project",
                )

            class RelaxedModel(firebase_ext_models.FbProject):
                model_config = ConfigDict(extra="ignore")

            # NOTE: we want to ignore extra fields from firebase
            valid_project = RelaxedModel.model_validate(obj=fb_project)
            valid_project = firebase_ext_models.FbProject.model_validate(obj=valid_project)

            self.update_project_on_firebase(project_ref, valid_project)

    def push_project_on_firebase(self):
        try:
            self._push_project_on_firebase()
        except Exception as ex:
            if isinstance(ex, ValidationException):
                logger.warning(
                    "push_to_firebase for project failed",
                    extra=log_extra({"project": self.project.pk}),
                    exc_info=True,
                )
                self.project.status_message = str(ex)
            elif isinstance(ex, SoftTimeLimitExceeded):
                logger.error(
                    "push_to_firebase for project failed due to SoftTimeLimitExceeded",
                    extra=log_extra({"project": self.project.pk}),
                    exc_info=True,
                )
                self.project.status_message = "Project sync to firebase timed out before completion"
            else:
                logger.error(
                    "push_to_firebase for project failed",
                    extra=log_extra({"project": self.project.pk}),
                    exc_info=True,
                )
                self.project.status_message = (
                    "Something unexpected happened! Please reach out on the MapSwipe slack for any further assistance."
                )

            self.project.update_firebase_push_status(FirebasePushStatusEnum.FAILED, False)
            # TODO(tnagorra): We also need to clear any intermediate values for groups, tasks and projects in firebase
            # NOTE: If project has already been published, we cannot update it's status
            if self.project.status_enum == Project.Status.READY_TO_PUBLISH:
                self.project.update_status(Project.Status.PUBLISHING_FAILED, False)
            self.project.save(
                update_fields=[
                    "status",
                    "status_message",
                    "firebase_push_status",
                    "firebase_last_pushed",
                ],
            )
        else:
            self.project.status_message = None
            self.project.update_firebase_push_status(FirebasePushStatusEnum.SUCCESS)
            if self.project.status_enum == Project.Status.READY_TO_PUBLISH:
                self.project.update_status(Project.Status.PUBLISHED, False)
            self.project.save(
                update_fields=[
                    "status",
                    "status_message",
                    "firebase_push_status",
                    "firebase_last_pushed",
                ],
            )

    # EXPORT

    def generate_exports(self):
        from apps.project.exports.exports import export_project_data

        # NOTE: Currently the logic is same for each project
        export_project_data(self.project)

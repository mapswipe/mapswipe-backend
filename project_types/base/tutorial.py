import json
import logging
import typing
from abc import ABC, abstractmethod

from django.core.files.base import ContentFile
from firebase_admin.db import Reference as FbReference
from pydantic import BaseModel, ConfigDict
from pyfirebase_mapswipe import models as firebase_models
from pyfirebase_mapswipe import utils as firebase_utils
from ulid import ULID

from apps.common.models import FirebasePushStatusEnum, IconEnum
from apps.tutorial.models import (
    Tutorial,
    TutorialAsset,
    TutorialInformationPageBlockTypeEnum,
    TutorialTask,
)
from main.config import Config
from main.logging import log_extra
from utils.common import compress_tasks

from .project import BaseProjectProperty

logger = logging.getLogger(__name__)


class InvalidTutorialPushException(Exception): ...


class BaseTutorialTaskProperty(BaseModel, ABC): ...


class BaseTutorial[
    ProjectPropertyTypeVar: BaseProjectProperty,
    TutorialTaskPropertyTypeVar: BaseTutorialTaskProperty,
](ABC):
    project_property_class: type[ProjectPropertyTypeVar]
    tutorial_task_property_class: type[TutorialTaskPropertyTypeVar]

    def __init__(self, tutorial: Tutorial):
        self.tutorial = tutorial
        self.project_type_specifics = self.project_property_class(**self.tutorial.project.project_type_specifics)

        self.firebase_helper = Config.FIREBASE_HELPER

    @classmethod
    def _inheritance_checks(cls):
        # FIXME(tnagorra): Find a better way to skip for base classes
        if cls.__name__.endswith("BaseTutorial"):
            # Skip check for the abstract class
            return

        missing_fields = []
        for attr_name in [
            "project_property_class",
            "tutorial_task_property_class",
        ]:
            if getattr(cls, attr_name, None) is None:
                missing_fields.append(attr_name)

        if missing_fields:
            raise NotImplementedError(f"Please define {','.join(missing_fields)} for {cls}")

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._inheritance_checks()

    @abstractmethod
    def get_task_specifics_for_firebase(self, task: TutorialTask, index: int) -> BaseModel: ...

    @abstractmethod
    def get_group_specifics_for_firebase(self) -> BaseModel: ...

    @abstractmethod
    def get_tutorial_specifics_for_firebase(self) -> BaseModel: ...

    def _save_tasks_as_json(self, grouped_tasks: typing.Any) -> None:
        """
        Generates a JSON file with all tasks and save it as a tutorial asset.
        Using this for debugging purpose of compressed tasks.
        """
        task_json = json.dumps(grouped_tasks, separators=(",", ":"))
        filename = f"tutorial_grouped_tasks_{self.tutorial.pk}.json"
        content_file = ContentFile(
            task_json.encode("utf-8"),
            filename,
        )
        TutorialAsset.objects.create(
            client_id=str(ULID()),
            tutorial=self.tutorial,
            file=content_file,
            file_size=content_file.size,
            mimetype=TutorialAsset.Mimetype.JSON,
            type=TutorialAsset.Type.DEBUG,
            # FIXME: Maybe create a internal user like mapswipe-bot
            created_by=self.tutorial.modified_by,
            modified_by=self.tutorial.modified_by,
        )

    def get_tutorial_group_key(self) -> int:
        return 101

    def get_task_sort_keys(self, existing_values: list[str]) -> list[str]:
        return existing_values

    def compress_tasks_on_firebase(self) -> bool:
        return False

    def create_tasks_on_firebase(self, task_ref: FbReference):
        tasks = TutorialTask.objects.filter(
            scenario__tutorial_id=self.tutorial.pk,
        ).order_by(
            *self.get_task_sort_keys(["scenario__scenario_page_number"]),
        )

        fb_tasks: list[dict[str, typing.Any]] = []
        index = 1
        for task in tasks.iterator():
            task_tutorial_specific_data = self.get_task_specifics_for_firebase(task, index)
            fb_tasks.append(firebase_utils.serialize(task_tutorial_specific_data))
            index += 1

        group_key = self.get_tutorial_group_key()

        grouped_tasks_dict: dict[int, list[dict[str, typing.Any]] | str] = {
            group_key: fb_tasks,
        }
        if self.compress_tasks_on_firebase():
            self._save_tasks_as_json(grouped_tasks_dict)
            grouped_tasks_dict = {group_key: compress_tasks(fb_tasks)}

        task_ref.set(value=grouped_tasks_dict)

    def create_groups_on_firebase(self, group_ref: FbReference):
        fb_groups: dict[str, dict[str, dict]] = {}

        group_key = self.get_tutorial_group_key()

        tasks_count = TutorialTask.objects.filter(scenario__tutorial_id=self.tutorial.pk).count()

        base_tutorial_specific_data = firebase_models.FbBaseTutorialGroup(
            finishedCount=0,
            groupId=group_key,
            numberOfTasks=tasks_count,
            progress=0,
            projectId=self.tutorial.firebase_id,
            requiredCount=0,
        )
        group_tutorial_specific_data = self.get_group_specifics_for_firebase()
        fb_groups[str(group_key)] = {
            **firebase_utils.serialize(base_tutorial_specific_data),
            **firebase_utils.serialize(group_tutorial_specific_data),
        }

        group_ref.set(value=fb_groups)

    def create_tutorial_on_firebase(self, tutorial_ref: FbReference):
        # NOTE: We are not reading data from group_ref as it's an expensive operation
        # FIXME(tnagorra): We need to check if the key exists later
        group_ref = self.firebase_helper.ref(
            Config.FirebaseKeys.tutorial_groups(self.tutorial.firebase_id),
        )
        # FIXME(tnagorra): We need to check if the key exists later
        task_ref = self.firebase_helper.ref(
            Config.FirebaseKeys.tutorial_tasks(self.tutorial.firebase_id),
        )

        self.create_tasks_on_firebase(task_ref)
        self.create_groups_on_firebase(group_ref)

        scenarios = self.tutorial.scenarios.all()
        informationPages = self.tutorial.information_pages.all()

        tutorial_data = firebase_models.FbBaseTutorial(
            exampleImage1=None,
            exampleImage2=None,
            contributorCount=0,
            informationPages=[
                firebase_models.FbInformationPage(
                    title=informationPage.title,
                    pageNumber=informationPage.page_number,
                    blocks=[
                        firebase_models.FbInformationPageBlock(
                            blockNumber=block.block_number,
                            blockType=TutorialInformationPageBlockTypeEnum(block.block_type).to_firebase(),
                            textDescription=block.text,
                            image=block.image.file.url if block.image else None,
                        )
                        for block in informationPage.blocks.all()
                    ],
                )
                for informationPage in informationPages
            ],
            lookFor=self.tutorial.project.look_for,
            name=self.tutorial.name,
            progress=0,
            # FIXME(tnagorra): We should add description in tutorial
            projectDetails=self.tutorial.project.description or "n/a",
            projectId=self.tutorial.firebase_id,
            projectTopicKey=self.tutorial.name.lower().strip(),
            status="tutorial",
            tutorialDraftId="",
            screens=[
                firebase_models.FbScreen(
                    hint=firebase_models.FbScreenBlock(
                        title=scenario.hint_title or "?",
                        description=scenario.hint_description or "?",
                        icon=str(scenario.hint_icon_enum.label)
                        if scenario.hint_icon_enum
                        else str(IconEnum.ALERT_OUTLINE.label),
                    ),
                    instructions=firebase_models.FbScreenBlock(
                        title=scenario.instructions_title,
                        description=scenario.instructions_description,
                        icon=str(scenario.instructions_icon_enum.label),
                    ),
                    success=firebase_models.FbScreenBlock(
                        title=scenario.success_title or "?",
                        description=scenario.success_description or "?",
                        icon=str(scenario.success_icon_enum.label)
                        if scenario.success_icon_enum
                        else str(IconEnum.ALERT_OUTLINE.label),
                    ),
                )
                for scenario in scenarios
            ],
        )

        tutorial_specific_data = self.get_tutorial_specifics_for_firebase()

        tutorial_ref.set(
            value={
                **firebase_utils.serialize(tutorial_data),
                **firebase_utils.serialize(tutorial_specific_data),
            },
        )

    def update_tutorial_on_firebase(self, tutorial_ref: FbReference, fb_tutorial: firebase_models.FbBaseTutorial):
        # NOTE: We are not reading data from group_ref as it's an expensive operation
        # FIXME(tnagorra): We need to check if the key exists later
        group_ref = self.firebase_helper.ref(
            Config.FirebaseKeys.project_groups(self.tutorial.firebase_id),
        )
        # FIXME(tnagorra): We need to check if the key exists later
        task_ref = self.firebase_helper.ref(
            Config.FirebaseKeys.project_tasks(self.tutorial.firebase_id),
        )

        self.create_tasks_on_firebase(task_ref)
        self.create_groups_on_firebase(group_ref)

        scenarios = self.tutorial.scenarios.all()
        informationPages = self.tutorial.information_pages.all()

        tutorial_data = firebase_models.FbBaseTutorial(
            exampleImage1=None,
            exampleImage2=None,
            contributorCount=0,
            informationPages=[
                firebase_models.FbInformationPage(
                    title=informationPage.title,
                    pageNumber=informationPage.page_number,
                    blocks=[
                        firebase_models.FbInformationPageBlock(
                            blockNumber=block.block_number,
                            blockType=TutorialInformationPageBlockTypeEnum(block.block_type).to_firebase(),
                            textDescription=block.text,
                            image=block.image.file.url if block.image else None,
                        )
                        for block in informationPage.blocks.all()
                    ],
                )
                for informationPage in informationPages
            ],
            lookFor=self.tutorial.project.look_for,
            name=self.tutorial.name,
            progress=0,
            # FIXME(tnagorra): We should add description in tutorial
            projectDetails=self.tutorial.project.description or "n/a",
            projectId=self.tutorial.firebase_id,
            projectTopicKey=self.tutorial.name.lower().strip(),
            status="tutorial",
            tutorialDraftId="",
            screens=[
                firebase_models.FbScreen(
                    hint=firebase_models.FbScreenBlock(
                        title=scenario.hint_title or "",
                        description=scenario.hint_description or "",
                        icon=str(scenario.hint_icon_enum.label) if scenario.hint_icon_enum else "",
                    ),
                    instructions=firebase_models.FbScreenBlock(
                        title=scenario.instructions_title or "",
                        description=scenario.instructions_description or "",
                        icon=str(scenario.instructions_icon_enum.label) if scenario.instructions_icon_enum else "",
                    ),
                    success=firebase_models.FbScreenBlock(
                        title=scenario.success_title or "",
                        description=scenario.success_description or "",
                        icon=str(scenario.success_icon_enum.label) if scenario.success_icon_enum else "",
                    ),
                )
                for scenario in scenarios
            ],
        )

        tutorial_specific_data = self.get_tutorial_specifics_for_firebase()

        tutorial_ref.update(
            value={
                **firebase_utils.serialize(tutorial_data),
                **firebase_utils.serialize(tutorial_specific_data),
            },
        )

    def push_tutorial_on_firebase(self):
        if self.tutorial.firebase_push_status_enum != FirebasePushStatusEnum.PENDING:
            logger.warning("%s - push_to_firebase called when push is not required", self.tutorial.pk)
            return

        self.tutorial.update_firebase_push_status(FirebasePushStatusEnum.PROCESSING)

        try:
            tutorial_ref = self.firebase_helper.ref(
                Config.FirebaseKeys.tutorial(self.tutorial.firebase_id),
            )
            fb_tutorial: typing.Any = tutorial_ref.get()

            if not self.tutorial.firebase_last_pushed:
                if fb_tutorial is not None:
                    logger.error(
                        "push_to_firebase found a tutorial already in firebase when creating a tutorial",
                        extra=log_extra({"tutorial": self.tutorial.pk}),
                    )
                    raise InvalidTutorialPushException
                self.create_tutorial_on_firebase(tutorial_ref)
            else:
                if fb_tutorial is None:
                    logger.error(
                        "push_to_firebase did not find tutorial in firebase when updating a tutorial",
                        extra=log_extra({"tutorial": self.tutorial.pk}),
                    )
                    raise InvalidTutorialPushException

                class RelaxedModel(firebase_models.FbBaseTutorial):
                    model_config = ConfigDict(extra="ignore")

                # NOTE: we want to ignore extra fields from firebase
                valid_tutorial = RelaxedModel.model_validate(obj=fb_tutorial)
                valid_tutorial = firebase_models.FbBaseTutorial.model_validate(obj=valid_tutorial)

                self.update_tutorial_on_firebase(tutorial_ref, valid_tutorial)
        except InvalidTutorialPushException:
            self.tutorial.update_firebase_push_status(FirebasePushStatusEnum.FAILED)
        except Exception:
            logger.error(
                "push_to_firebase failed",
                extra=log_extra({"tutorial": self.tutorial.pk}),
                exc_info=True,
            )
            self.tutorial.update_firebase_push_status(FirebasePushStatusEnum.FAILED)
        else:
            self.tutorial.update_firebase_push_status(FirebasePushStatusEnum.SUCCESS)

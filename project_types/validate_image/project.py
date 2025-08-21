import logging
import typing

from django.db import models
from pyfirebase_mapswipe import models as firebase_models

from apps.common.models import (
    AssetTypeEnum,
)
from apps.common.utils import get_absolute_uri
from apps.project.models import (
    Project,
    ProjectAsset,
    ProjectAssetInputTypeEnum,
    ProjectTask,
    ProjectTaskGroup,
)
from main.bulk_managers import BulkCreateManager
from project_types.base import project as base_project
from utils.asset_types.models import ObjectImageAnnotation, ObjectImageAssetProperty
from utils.common import Grouping, to_groups
from utils.custom_options.models import CustomOption

logger = logging.getLogger(__name__)


class ValidImage(typing.TypedDict):
    url: str
    file_name: str
    width: int | None
    height: int | None
    annotation: ObjectImageAnnotation | None


class ValidateImageSourceTypeEnum(models.TextChoices):
    DIRECT_IMAGES = "DIRECT_IMAGES", "Direct images"
    DATASET_FILE = "DATASET_FILE", "Dataset file"

    def to_firebase(self) -> firebase_models.FbEnumValidateImageInputType:
        match self:
            case ValidateImageSourceTypeEnum.DIRECT_IMAGES:
                return firebase_models.FbEnumValidateImageInputType.DIRECT_IMAGES
            case ValidateImageSourceTypeEnum.DATASET_FILE:
                return firebase_models.FbEnumValidateImageInputType.DATASET_FILE


class ValidateImageProjectProperty(base_project.BaseProjectProperty):
    source_type: ValidateImageSourceTypeEnum
    custom_options: list[CustomOption] | None = None


class ValidateImageProjectTaskGroupProperty(base_project.BaseProjectTaskGroupProperty): ...


class ValidateImageProjectTaskProperty(base_project.BaseProjectTaskProperty):
    url: str
    file_name: str
    width: int | None = None
    height: int | None = None
    annotation: ObjectImageAnnotation | None = None


class ValidateImageProject(
    base_project.BaseProject[
        ValidateImageProjectProperty,
        ValidateImageProjectTaskGroupProperty,
        ValidateImageProjectTaskProperty,
        list[ValidImage],
        Grouping[ValidImage],
    ],
):
    project_property_class = ValidateImageProjectProperty
    project_task_group_property_class = ValidateImageProjectTaskGroupProperty
    project_task_property_class = ValidateImageProjectTaskProperty

    def __init__(self, project: Project):
        super().__init__(project)

    def _validate_direct_images(self) -> list[ValidImage]:
        image_assets = ProjectAsset.usable_objects().filter(
            project_id=self.project.pk,
            type=AssetTypeEnum.INPUT,
            input_type=ProjectAssetInputTypeEnum.OBJECT_IMAGE,
            file__isnull=False,
        )

        image_assets_count = image_assets.count()
        if image_assets_count <= 0:
            raise Exception("There should be at least 1 image")
        if image_assets_count > 100:
            raise Exception("There should be at most 100 images")

        inputs: list[ValidImage] = []
        for image_asset in image_assets.iterator():
            valid_image: ValidImage = {
                "url": get_absolute_uri(image_asset.file),
                "file_name": image_asset.file.name,
                "width": None,
                "height": None,
                "annotation": None,
            }
            inputs.append(valid_image)
        return inputs

    def _validate_dataset_file(self) -> list[ValidImage]:
        image_assets = ProjectAsset.usable_objects().filter(
            project_id=self.project.pk,
            type=AssetTypeEnum.INPUT,
            input_type=ProjectAssetInputTypeEnum.OBJECT_IMAGE,
            external_url__isnull=False,
        )

        image_assets_count = image_assets.count()
        if image_assets_count <= 0:
            raise Exception("There should be at least 1 image")
        if image_assets_count > 10000:
            raise Exception("There should be at most 10000 images")

        inputs: list[ValidImage] = []
        for image_asset in image_assets.iterator():
            asset_specifics = ObjectImageAssetProperty(**image_asset.asset_type_specifics.get("object_image"))

            annotations = asset_specifics.annotations
            if annotations:
                for annotation in annotations:
                    valid_image: ValidImage = {
                        "url": image_asset.external_url,
                        "file_name": asset_specifics.image.file_name,
                        "width": asset_specifics.image.width,
                        "height": asset_specifics.image.height,
                        "annotation": annotation,
                    }
                    inputs.append(valid_image)
            else:
                valid_image: ValidImage = {
                    "url": image_asset.external_url,
                    "file_name": asset_specifics.image.file_name,
                    "width": None,
                    "height": None,
                    "annotation": None,
                }
                inputs.append(valid_image)
        return inputs

    @typing.override
    def validate(self) -> list[ValidImage]:
        """Validate project before creating groups"""
        # FIXME(tnagora): rename VALIDATING_GEOMETRY to VALIDATING_INPUT
        self.project.update_processing_status(Project.ProcessingStatus.VALIDATING_GEOMETRY, True)

        if self.project_type_specifics.source_type == ValidateImageSourceTypeEnum.DIRECT_IMAGES:
            return self._validate_direct_images()

        if self.project_type_specifics.source_type == ValidateImageSourceTypeEnum.DATASET_FILE:
            return self._validate_dataset_file()

        raise Exception("Invalid source type")

    @typing.override
    def create_groups(self, resp: list[ValidImage]):
        self.project.update_processing_status(Project.ProcessingStatus.GENERATING_GROUPS_AND_TASKS, True)
        raw_groups = to_groups(resp, self.project.group_size)

        for group_key, raw_group in raw_groups.items():
            new_group = ProjectTaskGroup.objects.create(
                firebase_id=group_key,
                project_id=self.project.pk,
                number_of_tasks=0,
                progress=0,
                finished_count=0,
                required_count=0,
                project_type_specifics=self.project_task_group_property_class().model_dump(),
            )

            # Create new tasks for this group
            total_tasks = self.create_tasks(new_group, raw_group)
            logger.info("Created %s tasks for group: %s", total_tasks, new_group.pk)

    @typing.override
    def create_tasks(self, group: ProjectTaskGroup, raw_group: Grouping[ValidImage]) -> int:
        """Create tasks for a group."""
        bulk_mgr = BulkCreateManager(chunk_size=1000)

        tasks_count = 0
        features = raw_group["features"]
        f_ids = raw_group["feature_ids"]

        for i, f_id in enumerate(f_ids):
            feature = features[i]

            bulk_mgr.add(
                ProjectTask(
                    firebase_id=f"t{f_id}",
                    task_group_id=group.pk,
                    geometry=None,
                    # FIXME(tnagorra): Do we need to define all of these here?
                    project_type_specifics=self.project_task_property_class(
                        url=feature["url"],
                        file_name=feature["file_name"],
                        width=feature["width"],
                        height=feature["height"],
                        annotation=feature["annotation"],
                    ).model_dump(),
                ),
            )
            tasks_count += 1

        bulk_mgr.done()
        return tasks_count

    @typing.override
    def post_create_groups(self): ...

    # FIREBASE

    @typing.override
    def get_task_specifics_for_firebase(self, task):
        task_specifics = self.project_task_property_class(
            **task.project_type_specifics,
        )
        return firebase_models.FbMappingTaskValidateImageCreateOnlyInput(
            taskId=task.firebase_id,
            url=task_specifics.url,
            annotationId=task_specifics.annotation.id if task_specifics.annotation else None,
            # FIXME(tnagorra): Not sure if list is converted to tuple
            bbox=list(task_specifics.annotation.bbox)
            if task_specifics.annotation and task_specifics.annotation.bbox
            else None,
            segmentation=task_specifics.annotation.segmentation
            if task_specifics.annotation and task_specifics.annotation.segmentation
            else None,
            height=task_specifics.height,
            width=task_specifics.width,
            fileName=task_specifics.file_name,
        )

    @typing.override
    def get_group_specifics_for_firebase(self, group):
        return firebase_models.FbMappingGroupValidateImageCreateOnlyInput(
            # TODO(tnagorra): Add fields here
            groupId=group.firebase_id,
        )

    @typing.override
    def get_project_specifics_for_firebase(self):
        custom_opts = self.project_type_specifics.custom_options
        return firebase_models.FbProjectValidateImageCreateOnlyInput(
            customOptions=[
                firebase_models.FbObjCustomOption(
                    title=opt.title,
                    description=opt.description,
                    value=opt.value,
                    icon=str(opt.icon.label),
                    iconColor=opt.icon_color,
                    subOptions=[
                        firebase_models.FbBaseObjCustomSubOption(
                            value=sub_opt.value,
                            description=sub_opt.description,
                        )
                        for sub_opt in opt.sub_options
                    ]
                    if opt.sub_options is not None
                    else None,
                )
                for opt in custom_opts
            ]
            if custom_opts is not None
            else None,
        )

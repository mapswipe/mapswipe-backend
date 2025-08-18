# pyright: reportUninitializedInstanceVariable=false
import typing
from warnings import deprecated

import ulid
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext, gettext_lazy
from django_choices_field import IntegerChoicesField
from django_stubs_ext.db.models.manager import RelatedManager
from pyfirebase_mapswipe import models as firebase_models

from apps.common.models import FirebasePushResource, IconEnum, UserResource
from apps.project.models import CommonAsset, Project
from main.fields import OverwritableFileField


class UploadHelper:
    @deprecated("This is kept because it's referenced in migrations")
    @staticmethod
    def information_page_block_image(instance: "TutorialInformationPageBlock", filename: str):
        return f"tutorial/{instance.page.tutorial_id}/block-image/{ulid.ULID()!s}/{filename}"

    @staticmethod
    def tutorial_asset(instance: "TutorialAsset", filename: str):
        return f"tutorial/{instance.tutorial_id}/asset/{instance.type}/{ulid.ULID()!s}/{filename}"


class TutorialStatusEnum(models.IntegerChoices):
    DRAFT = 10, "Draft"
    """
    Draft tutorials are not ready to be attached to projects.
    """

    PUBLISHED = 20, "Published"
    """
    "Published" tutorials can be attached to projects.
    """

    ARCHIVED = 30, "Archived"
    """
    "Archived" tutorials cannot be attached to new projects.
    "Archived" tutorials cannot be "un-archived".
    """

    DISCARDED = 40, "Discarded"
    """
    "Discarded" tutorials cannot be attached to new projects.
    "Discarded" tutorials cannot be "un-discarded".
    """


def generate_tutorial_firebase_id():
    return f"tutorial_{ulid.ULID()}"


class Tutorial(UserResource, FirebasePushResource):  # type: ignore[reportIncompatibleVariableOverride]
    Status = TutorialStatusEnum

    # FIXME(tnagorra): We might need to rename this field
    project: Project = models.ForeignKey(  # type: ignore[reportAssignmentType]
        Project,
        on_delete=models.PROTECT,
        related_name="+",
        help_text=gettext_lazy("Project this tutorial is referring to."),
    )

    name = models.CharField(max_length=255)
    status: int = IntegerChoicesField(  # type: ignore[reportAssignmentType]
        choices_enum=TutorialStatusEnum,
        default=TutorialStatusEnum.DRAFT,
    )

    firebase_id = models.CharField(max_length=40, unique=True, default=generate_tutorial_firebase_id)

    # Type hints
    project_id: int
    scenarios: RelatedManager["TutorialScenarioPage"]
    information_pages: RelatedManager["TutorialInformationPage"]

    @property
    def status_enum(self) -> TutorialStatusEnum:
        return TutorialStatusEnum(self.status)


class TutorialAsset(UserResource, CommonAsset):  # type: ignore[reportIncompatibleVariableOverride]
    tutorial: Tutorial = models.ForeignKey(  # type: ignore[reportAssignmentType]
        Tutorial,
        on_delete=models.CASCADE,
        related_name="+",
    )

    file = OverwritableFileField(
        upload_to=UploadHelper.tutorial_asset,
        help_text=gettext_lazy("The file associated with the asset"),
    )

    # Type hints
    tutorial_id: int


class TutorialScenarioPage(UserResource):
    tutorial: Tutorial = models.ForeignKey(  # type: ignore[reportAssignmentType]
        Tutorial,
        on_delete=models.CASCADE,
        related_name="scenarios",
    )

    scenario_page_number = models.PositiveSmallIntegerField()

    instructions_description = models.CharField(max_length=255)
    instructions_icon = IntegerChoicesField(choices_enum=IconEnum)
    instructions_title = models.CharField(max_length=255)

    hint_description = models.CharField(max_length=255, null=True, blank=True)
    hint_icon = IntegerChoicesField(choices_enum=IconEnum, null=True, blank=True)
    hint_title = models.CharField(max_length=255, null=True, blank=True)

    success_description = models.CharField(max_length=255, null=True, blank=True)
    success_icon = IntegerChoicesField(choices_enum=IconEnum, null=True, blank=True)
    success_title = models.CharField(max_length=255, null=True, blank=True)

    # Type hints
    tutorial_id: int
    tasks: RelatedManager["TutorialTask"]

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        constraints = [
            models.UniqueConstraint(fields=["tutorial", "scenario_page_number"], name="unique_scenario_on_tutorials"),
        ]

    @property
    def instructions_icon_enum(self) -> IconEnum:
        return IconEnum(self.instructions_icon)

    @property
    def hint_icon_enum(self) -> IconEnum | None:
        if self.hint_icon:
            return IconEnum(self.hint_icon)
        return None

    @property
    def success_icon_enum(self) -> IconEnum | None:
        if self.success_icon:
            return IconEnum(self.success_icon)
        return None

    @typing.override
    def __str__(self):
        return self.scenario_page_number


class TutorialTask(UserResource):
    scenario: TutorialScenarioPage = models.ForeignKey(  # type: ignore[reportAssignmentType]
        TutorialScenarioPage,
        on_delete=models.CASCADE,
        related_name="tasks",
    )

    # FIXME(tnagorra): attach project?

    reference = models.PositiveSmallIntegerField()

    # FIXME(tnagorra): Do we need to save project_type here as well?
    project_type_specifics = models.JSONField()

    # Type hints
    scenario_id: int

    @typing.override
    def __str__(self):
        return str(self.pk)


class TutorialInformationPage(UserResource):
    tutorial: Tutorial = models.ForeignKey(  # type: ignore[reportAssignmentType]
        Tutorial,
        on_delete=models.CASCADE,
        related_name="information_pages",
    )
    title = models.CharField(max_length=255)
    page_number = models.PositiveSmallIntegerField()

    # Type hints
    tutorial_id: int
    blocks: RelatedManager["TutorialInformationPageBlock"]

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        constraints = [
            models.UniqueConstraint(fields=["tutorial", "page_number"], name="unique_page_number_on_tutorial"),
        ]

    @typing.override
    def __str__(self):
        return self.title


class TutorialInformationPageBlockTypeEnum(models.IntegerChoices):
    TEXT = 1, "Text"
    IMAGE = 2, "Image"

    def to_firebase(self) -> firebase_models.FbEnumInformationPageBlockType:
        match self:
            case TutorialInformationPageBlockTypeEnum.TEXT:
                return firebase_models.FbEnumInformationPageBlockType.TEXT
            case TutorialInformationPageBlockTypeEnum.IMAGE:
                return firebase_models.FbEnumInformationPageBlockType.IMAGE


class TutorialInformationPageBlock(UserResource):
    Type = TutorialInformationPageBlockTypeEnum

    page: TutorialInformationPage = models.ForeignKey(  # type: ignore[reportAssignmentType]
        TutorialInformationPage,
        on_delete=models.CASCADE,
        related_name="blocks",
    )

    block_number = models.PositiveSmallIntegerField()
    block_type = IntegerChoicesField(choices_enum=TutorialInformationPageBlockTypeEnum)
    # NOTE: Previously was text_description
    text = models.TextField(null=True, blank=True)
    image: "TutorialAsset | None" = models.ForeignKey(  # type: ignore[reportAssignmentType]
        "tutorial.TutorialAsset",
        related_name="+",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    # Type hints
    page_id: int

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        constraints = [
            models.UniqueConstraint(fields=["page", "block_number"], name="unique_block_number_on_page"),
        ]

    @typing.override
    def __str__(self):
        return f"page_id={self.page_id}, block_number={self.block_number}, block_type={self.block_type}"

    @property
    def block_type_enum(self):
        return TutorialInformationPageBlockTypeEnum(self.block_type)

    @typing.override
    def clean(self):
        if self.block_type_enum == TutorialInformationPageBlockTypeEnum.TEXT and (self.text is None or self.text == ""):
            raise ValidationError(gettext("Text should be provided for text block"))
        if self.block_type_enum == TutorialInformationPageBlockTypeEnum.IMAGE and self.image is None:
            raise ValidationError(gettext("Image should be provided for image block"))

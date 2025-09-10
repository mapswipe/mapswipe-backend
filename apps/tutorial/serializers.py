import typing

import pydantic
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext
from rest_framework import serializers

from apps.common.models import AssetMimetypeEnum, FirebasePushStatusEnum
from apps.common.serializers import CommonAssetSerializer, DrfContextType, UserResourceSerializer
from apps.project.models import Project, ProjectTypeEnum
from project_types.store import get_tutorial_task_property
from utils.common import clean_up_none_keys
from utils.graphql.drf import handle_pydantic_validation_error

from .models import (
    Tutorial,
    TutorialAsset,
    TutorialAssetInputTypeEnum,
    TutorialInformationPage,
    TutorialInformationPageBlock,
    TutorialScenarioPage,
    TutorialTask,
)
from .tasks import push_tutorial_to_firebase

if typing.TYPE_CHECKING:
    from django.core.files.base import ContentFile


class TutorialTaskSerializerContextType(DrfContextType):
    scenario: TutorialScenarioPage


class TutorialTaskSerializer(UserResourceSerializer[TutorialTask, TutorialTaskSerializerContextType]):
    id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = TutorialTask
        fields = (
            "id",
            "reference",
            "project_type_specifics",
        )

    def _validate_project_type_specifics(self, attrs: dict[str, typing.Any]):
        if (tutorial := self.context.get("tutorial")) is None:
            return

        project_type = tutorial.project.project_type
        if project_type is None:
            raise serializers.ValidationError(
                {
                    "project_type": gettext("Project type is required."),
                },
            )

        project_type_label = ProjectTypeEnum.get_display(project_type)

        project_property = get_tutorial_task_property(project_type)
        if project_property is None:
            raise serializers.ValidationError(
                {
                    "project_type_specifics": gettext("Given project type is not handled: %s") % project_type_label,
                },
            )

        field_name, pydantic_model = project_property
        raw_project_type_specifics = attrs.get("project_type_specifics")

        project_type_specifics = None
        if raw_project_type_specifics is not None:
            project_type_specifics = raw_project_type_specifics.get(field_name)
        elif self.instance is not None:
            project_type_specifics = self.instance.project_type_specifics

        if project_type_specifics is None:
            raise serializers.ValidationError(
                {
                    "project_type_specifics": gettext("Configuration not provided for %s") % project_type_label,
                },
            )

        # XXX: Clean up nullable keys
        project_type_specifics = clean_up_none_keys(project_type_specifics)

        try:
            pydantic_model.model_validate(
                project_type_specifics,
            )
        except pydantic.ValidationError as pydantic_error:
            raise handle_pydantic_validation_error("project_type_specifics", pydantic_error) from None

        attrs["project_type_specifics"] = project_type_specifics

    @typing.override
    def validate(self, attrs: dict[str, typing.Any]):
        self._validate_project_type_specifics(attrs)
        return super().validate(attrs)

    @typing.override
    def create(self, validated_data: dict[typing.Any, typing.Any]):
        validated_data["scenario"] = self.context["scenario"]
        return super().create(validated_data)

    @typing.override
    def update(self, instance: TutorialTask, validated_data: dict[typing.Any, typing.Any]):
        validated_data["scenario"] = self.context["scenario"]
        return super().update(instance, validated_data)


class TutorialScenarioPageContextType(DrfContextType):
    tutorial: Tutorial


class TutorialScenarioPageSerializer(
    UserResourceSerializer[TutorialScenarioPage, TutorialScenarioPageContextType],
):
    id = serializers.IntegerField(required=False, allow_null=True)
    tasks = TutorialTaskSerializer(many=True)

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = TutorialScenarioPage
        fields = (
            "id",
            "scenario_page_number",
            "instructions_description",
            "instructions_icon",
            "instructions_title",
            "hint_description",
            "hint_icon",
            "hint_title",
            "success_description",
            "success_icon",
            "success_title",
            "tasks",
        )

    @typing.override
    def create(self, validated_data: dict[typing.Any, typing.Any]):
        tasks_data = self.initial_data["tasks"]
        validated_data.pop("tasks")

        validated_data["tutorial"] = self.context["tutorial"]
        scenario = super().create(validated_data)

        for task_data in tasks_data:
            task_serializer = TutorialTaskSerializer(
                data=task_data,
                context={
                    **self.context,
                    "scenario": scenario,
                },
            )
            task_serializer.is_valid(raise_exception=True)
            task_serializer.save()

        return scenario

    @typing.override
    def update(self, instance: TutorialScenarioPage, validated_data: dict[typing.Any, typing.Any]):
        tasks_data = self.initial_data.get("tasks") or []
        validated_data.pop("tasks", None)

        validated_data["tutorial"] = self.context["tutorial"]
        scenario = super().update(instance, validated_data)

        task_qs = TutorialTask.objects.filter(
            scenario=scenario.pk,
        )

        for task_data in tasks_data:
            task_id = task_data.pop("id", None)
            task_instance = None
            if task_id is not None:
                task_instance = get_object_or_404(task_qs, id=task_id)

            task_serializer = TutorialTaskSerializer(
                data=task_data,
                instance=task_instance,
                context={
                    **self.context,
                    "scenario": scenario,
                },
            )
            task_serializer.is_valid(raise_exception=True)
            task_serializer.save()

        return scenario


class TutorialInformationPageBlockContextType(DrfContextType):
    page: TutorialScenarioPage


class TutorialInformationPageBlockSerializer(
    UserResourceSerializer[TutorialInformationPageBlock, TutorialInformationPageBlockContextType],
):
    id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = TutorialInformationPageBlock
        fields = (
            "id",
            "block_number",
            "block_type",
            "text",
            "image",
        )

    @typing.override
    def create(self, validated_data: dict[typing.Any, typing.Any]):
        validated_data["page"] = self.context["page"]
        return super().create(validated_data)

    @typing.override
    def update(self, instance: TutorialInformationPageBlock, validated_data: dict[typing.Any, typing.Any]):
        validated_data["page"] = self.context["page"]
        return super().update(instance, validated_data)


class TutorialInformationPageContextType(DrfContextType):
    tutorial: Tutorial


class TutorialInformationPageSerializer(
    UserResourceSerializer[TutorialInformationPage, TutorialInformationPageContextType],
):
    id = serializers.IntegerField(required=False, allow_null=True)
    blocks = TutorialInformationPageBlockSerializer(many=True)

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = TutorialInformationPage
        fields = (
            "id",
            "title",
            "page_number",
            "blocks",
        )

    @typing.override
    def create(self, validated_data: dict[typing.Any, typing.Any]):
        blocks_data = self.initial_data["blocks"]
        validated_data.pop("blocks")

        validated_data["tutorial"] = self.context["tutorial"]
        page = super().create(validated_data)

        for block_data in blocks_data:
            block_serializer = TutorialInformationPageBlockSerializer(
                data=block_data,
                context={
                    **self.context,
                    "page": page,
                },
            )
            block_serializer.is_valid(raise_exception=True)
            block_serializer.save()

        return page

    @typing.override
    def update(self, instance: TutorialInformationPage, validated_data: dict[typing.Any, typing.Any]):
        blocks_data = self.initial_data["blocks"] or []
        validated_data.pop("blocks", None)

        validated_data["tutorial"] = self.context["tutorial"]
        page = super().update(instance, validated_data)

        block_qs = TutorialInformationPageBlock.objects.filter(
            page=page.pk,
        )

        for block_data in blocks_data:
            block_id = block_data.pop("id", None)
            block_instance = None
            if block_id is not None:
                block_instance = get_object_or_404(block_qs, id=block_id)

            block_serializer = TutorialInformationPageBlockSerializer(
                data=block_data,
                instance=block_instance,
                context={
                    **self.context,
                    "page": page,
                },
            )
            block_serializer.is_valid(raise_exception=True)
            block_serializer.save()

        return page


VALID_TUTORIAL_STATUS_TRANSITIONS: set[tuple[Tutorial.Status, Tutorial.Status]] = set(
    [
        (Tutorial.Status.DRAFT, Tutorial.Status.READY_TO_PUBLISH),
        (Tutorial.Status.DRAFT, Tutorial.Status.DISCARDED),
        (Tutorial.Status.PUBLISHING_FAILED, Tutorial.Status.DISCARDED),
        (Tutorial.Status.PUBLISHING_FAILED, Tutorial.Status.READY_TO_PUBLISH),
        # (Tutorial.Status.READY_TO_PUBLISH, Tutorial.Status.PUBLISHING_FAILED),    # auto on bg
        # (Tutorial.Status.READY_TO_PUBLISH, Tutorial.Status.PUBLISHED),            # auto on bg
        (Tutorial.Status.PUBLISHED, Tutorial.Status.ARCHIVED),
        (Tutorial.Status.ARCHIVED, Tutorial.Status.PUBLISHED),
    ],
)


# NOTE: Make sure this matches with the strawberry Input ./graphql/inputs.py
class TutorialCreateSerializer(UserResourceSerializer[Tutorial]):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Tutorial
        fields = (
            "name",
            "project",
        )

    def validate_project(self, project: Project) -> Project:
        if self.instance and self.instance.project.project_type_enum != project.project_type_enum:
            raise serializers.ValidationError(
                gettext("Existing tutorial project type '%s' does not match new project type '%s'")
                % (
                    Project.Type(self.instance.project.project_type_enum).label,
                    Project.Type(project.project_type_enum).label,
                ),
            )
        return project


# NOTE: Make sure this matches with the strawberry Input ./graphql/inputs.py
class TutorialUpdateSerializer(UserResourceSerializer[Tutorial]):
    scenarios = TutorialScenarioPageSerializer(many=True)
    information_pages = TutorialInformationPageSerializer(many=True)

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Tutorial
        fields = (
            "name",
            "information_pages",
            "scenarios",
        )

    @typing.override
    def create(self, validated_data: dict[typing.Any, typing.Any]):
        scenarios_data = self.initial_data["scenarios"]
        information_pages_data = self.initial_data["information_pages"]
        validated_data.pop("scenarios")
        validated_data.pop("information_pages")
        tutorial = super().create(validated_data)

        for scenario_data in scenarios_data:
            scenario_serializer = TutorialScenarioPageSerializer(
                data=scenario_data,
                context={
                    **self.context,
                    "tutorial": tutorial,
                },
            )
            scenario_serializer.is_valid(raise_exception=True)
            scenario_serializer.save()

        for information_page_data in information_pages_data:
            information_page_serializer = TutorialInformationPageSerializer(
                data=information_page_data,
                context={
                    **self.context,
                    "tutorial": tutorial,
                },
            )
            information_page_serializer.is_valid(raise_exception=True)
            information_page_serializer.save()

        return tutorial

    @typing.override
    def update(self, instance: Tutorial, validated_data: dict[typing.Any, typing.Any]):
        old_status_enum = instance.status_enum
        scenarios_data = self.initial_data.get("scenarios") or []
        information_pages_data = self.initial_data.get("information_pages") or []
        validated_data.pop("scenarios", None)
        validated_data.pop("information_pages", None)

        updated_tutorial = super().update(instance, validated_data)

        scenario_qs = TutorialScenarioPage.objects.filter(
            tutorial=updated_tutorial.pk,
        )
        information_page_qs = TutorialInformationPage.objects.filter(
            tutorial=updated_tutorial.pk,
        )

        for scenario_data in scenarios_data:
            scenario_id = scenario_data.pop("id", None)
            scenario_instance = None
            if scenario_id is not None:
                scenario_instance = get_object_or_404(scenario_qs, id=scenario_id)
            scenario_serializer = TutorialScenarioPageSerializer(
                data=scenario_data,
                instance=scenario_instance,
                context={
                    **self.context,
                    "tutorial": updated_tutorial,
                },
            )
            scenario_serializer.is_valid(raise_exception=True)
            scenario_serializer.save()

        for information_page_data in information_pages_data:
            information_page_id = information_page_data.pop("id", None)
            information_page_instance = None
            if information_page_id is not None:
                information_page_instance = get_object_or_404(information_page_qs, id=information_page_id)
            information_page_serializer = TutorialInformationPageSerializer(
                data=information_page_data,
                instance=information_page_instance,
                context={
                    **self.context,
                    "tutorial": updated_tutorial,
                },
            )
            information_page_serializer.is_valid(raise_exception=True)
            information_page_serializer.save()

        if old_status_enum == Tutorial.Status.PUBLISHED and updated_tutorial.status_enum == Tutorial.Status.PUBLISHED:
            updated_tutorial.update_firebase_push_status(FirebasePushStatusEnum.PENDING)
            transaction.on_commit(lambda: push_tutorial_to_firebase.delay(updated_tutorial.pk))

        return updated_tutorial


# NOTE: Make sure this matches with the strawberry Input ./graphql/inputs.py
class TutorialAssetSerializer(CommonAssetSerializer, UserResourceSerializer[TutorialAsset]):  # type: ignore[reportIncompatibleVariableOverride]
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = TutorialAsset
        fields = (
            "file",
            "input_type",
            "tutorial",
            "external_url",
        )

    def _validate_information_block_image(
        self,
        attrs: dict[str, typing.Any],
        mimetype: AssetMimetypeEnum | None,
    ) -> None:
        file: ContentFile[bytes] | None = attrs.get("file")
        if not file:
            raise ValidationError(
                {
                    "file": "Required field file is not provided.",
                },
            )

        if not mimetype or mimetype not in [
            AssetMimetypeEnum.IMAGE_GIF,
            AssetMimetypeEnum.IMAGE_JPEG,
            AssetMimetypeEnum.IMAGE_PNG,
        ]:
            raise ValidationError(
                {
                    "file": "Mimetype is should either be a Jpeg, Png or Gif",
                },
            )

    @typing.override
    def validate(self, attrs: dict[str, typing.Any]) -> dict[str, typing.Any]:
        attrs = super().validate(attrs)

        input_type = attrs.get("input_type")
        mimetype = attrs.get("mimetype")

        input_type_enum = TutorialAssetInputTypeEnum(input_type)
        mimetype_enum = AssetMimetypeEnum(mimetype) if mimetype else None

        match input_type_enum:
            case TutorialAssetInputTypeEnum.INFORMATION_BLOCK_IMAGE:
                self._validate_information_block_image(attrs, mimetype_enum)
            case _:
                typing.assert_never(input_type_enum)

        return attrs


class TutorialStatusUpdateSerializer(UserResourceSerializer[Tutorial]):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Tutorial
        fields = ("status",)

    def validate_status(self, new_status: Tutorial.Status | int) -> Tutorial.Status:
        assert self.instance is not None, "Tutorial does not exist."

        if not isinstance(new_status, Tutorial.Status):
            new_status = Tutorial.Status(new_status)

        if (
            self.instance.status_enum != new_status
            and (self.instance.status_enum, new_status) not in VALID_TUTORIAL_STATUS_TRANSITIONS
        ):
            raise serializers.ValidationError(
                gettext("Tutorial status cannot be changed from %s to %s")
                % (
                    self.instance.status_enum.label,
                    new_status.label,
                ),
            )
        return new_status

    @typing.override
    def update(self, instance: Tutorial, validated_data: dict[typing.Any, typing.Any]):
        old_status_enum = instance.status_enum
        updated_tutorial = super().update(instance, validated_data)

        if (
            old_status_enum != Tutorial.Status.READY_TO_PUBLISH
            and updated_tutorial.status_enum == Tutorial.Status.READY_TO_PUBLISH
        ):
            updated_tutorial.update_firebase_push_status(FirebasePushStatusEnum.PENDING)
            transaction.on_commit(lambda: push_tutorial_to_firebase.delay(updated_tutorial.pk))

        return updated_tutorial

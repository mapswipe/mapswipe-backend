import typing

import pydantic
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext
from rest_framework import serializers

from apps.common.serializers import DrfContextType, UserResourceSerializer
from apps.project.models import ProjectTypeEnum
from apps.tutorial.project_types.tile_map_service.compare import tutorial as compare_tutorial
from apps.tutorial.project_types.tile_map_service.completeness import tutorial as completeness_tutorial
from apps.tutorial.project_types.tile_map_service.find import tutorial as find_tutorial
from utils.common import clean_up_none_keys
from utils.graphql.drf import handle_pydantic_validation_error

from .models import Tutorial, TutorialInformationPage, TutorialInformationPageBlock, TutorialScenarioPage, TutorialTask


# FIXME(tnagorra): Move this to utils
def get_tutorial_task_property(project_type: ProjectTypeEnum | None):
    if project_type is None:
        return None
    if project_type == ProjectTypeEnum.COMPARE:
        return ("compare", compare_tutorial.CompareTutorialTaskProperty)
    if project_type == ProjectTypeEnum.FIND:
        return ("find", find_tutorial.FindTutorialTaskProperty)
    if project_type == ProjectTypeEnum.COMPLETENESS:
        return ("completeness", completeness_tutorial.CompletenessTutorialTaskProperty)
    typing.assert_never(project_type)


class TutorialTaskSerializerContextType(DrfContextType):
    scenario: TutorialScenarioPage


class TutorialTaskSerializer(UserResourceSerializer[TutorialTask, TutorialTaskSerializerContextType]):
    id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = TutorialTask
        fields = (
            "id",
            "client_id",
            "reference",
            "project_type_specifics",
        )

    def _validate_project_type_specifics(self, attrs: dict[str, typing.Any]):
        if (tutorial := self.context.get("tutorial")) is None:
            return

        # FIXME: Make this type-safe
        project_type = tutorial.project.project_type

        # TODO(tnagorra): Get this project_type from the associated project
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
            "client_id",
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
            "client_id",
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
            "client_id",
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


class TutorialSerializer(UserResourceSerializer[Tutorial]):
    scenarios = TutorialScenarioPageSerializer(many=True)
    information_pages = TutorialInformationPageSerializer(many=True)

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Tutorial
        fields = (
            "client_id",
            "project",
            "is_draft",
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
        scenarios_data = self.initial_data["scenarios"] or []
        information_pages_data = self.initial_data["information_pages"] or []
        validated_data.pop("scenarios", None)
        validated_data.pop("information_pages", None)
        tutorial = super().update(instance, validated_data)

        scenario_qs = TutorialScenarioPage.objects.filter(
            tutorial=tutorial.pk,
        )
        information_page_qs = TutorialInformationPage.objects.filter(
            tutorial=tutorial.pk,
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
                    "tutorial": tutorial,
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
                    "tutorial": tutorial,
                },
            )
            information_page_serializer.is_valid(raise_exception=True)
            information_page_serializer.save()

        return tutorial

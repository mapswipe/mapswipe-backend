import typing

from apps.common.serializers import DrfContextType, UserResourceSerializer

from .models import Tutorial, TutorialInformationPage, TutorialInformationPageBlock, TutorialScenarioPage, TutorialTask


class TutorialTaskSerializerContextType(DrfContextType):
    scenario: TutorialScenarioPage


class TutorialTaskSerializer(UserResourceSerializer[TutorialTask, TutorialTaskSerializerContextType]):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = TutorialTask
        fields = (
            "reference",
            # TODO(tnagorra): Implement stricter project_type_specifics
            "project_type_specifics",
        )

    @typing.override
    def create(self, validated_data: dict[typing.Any, typing.Any]):
        validated_data["scenario"] = self.context["scenario"]
        return super().create(validated_data)


class TutorialScenarioPageContextType(DrfContextType):
    tutorial: Tutorial


class TutorialScenarioPageSerializer(
    UserResourceSerializer[TutorialScenarioPage, TutorialScenarioPageContextType],
):
    tasks = TutorialTaskSerializer(many=True)

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = TutorialScenarioPage
        fields = (
            "scenario_id",
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
        tasks_data = validated_data.pop("tasks")

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


class TutorialInformationPageBlockContextType(DrfContextType):
    page: TutorialScenarioPage


class TutorialInformationPageBlockSerializer(
    UserResourceSerializer[TutorialInformationPageBlock, TutorialInformationPageBlockContextType],
):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = TutorialInformationPageBlock
        fields = (
            "block_number",
            "block_type",
            "text",
            "image",
        )

    @typing.override
    def create(self, validated_data: dict[typing.Any, typing.Any]):
        validated_data["page"] = self.context["page"]
        return super().create(validated_data)


class TutorialInformationPageContextType(DrfContextType):
    tutorial: Tutorial


class TutorialInformationPageSerializer(
    UserResourceSerializer[TutorialInformationPage, TutorialInformationPageContextType],
):
    blocks = TutorialInformationPageBlockSerializer(many=True)

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = TutorialInformationPage
        fields = (
            "title",
            "page_number",
            "blocks",
        )

    @typing.override
    def create(self, validated_data: dict[typing.Any, typing.Any]):
        blocks_data = validated_data.pop("blocks")

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


class TutorialSerializer(UserResourceSerializer[Tutorial]):
    scenarios = TutorialScenarioPageSerializer(many=True)
    information_pages = TutorialInformationPageSerializer(many=True)

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Tutorial
        fields = (
            "project",
            "is_draft",
            "information_pages",
            "scenarios",
        )

    @typing.override
    def create(self, validated_data: dict[typing.Any, typing.Any]):
        scenarios_data = validated_data.pop("scenarios")
        information_pages_data = validated_data.pop("information_pages")
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
            # blocks_data = information_page_data.pop("blocks")
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

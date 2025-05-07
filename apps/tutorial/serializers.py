from apps.common.serializers import UserResourceSerializer

from .models import Tutorial, TutorialInformationPage, TutorialInformationPageBlock, TutorialScenarioPage, TutorialTask


class TutorialTaskCreateSerializer(UserResourceSerializer[TutorialTask]):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = TutorialTask
        fields = (
            "scenario",
            "reference",
            # TODO(tnagorra): Implement project_type_specifics
            # "project_type_specifics",
        )


class TutorialScenarioPageCreateSerializer(UserResourceSerializer[TutorialScenarioPage]):
    tasks = TutorialTaskCreateSerializer(many=True)

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = TutorialScenarioPage
        fields = (
            "tutorial",
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
        )


class TutorialInformationPageBlockCreateSerializer(UserResourceSerializer[TutorialInformationPageBlock]):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = TutorialInformationPageBlock
        fields = (
            "page",
            "block_number",
            "block_type",
            "text",
            "image",
        )


class TutorialInformationPageCreateSerializer(UserResourceSerializer[TutorialInformationPage]):
    blocks = TutorialInformationPageBlockCreateSerializer(many=True)

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = TutorialInformationPage
        fields = (
            "tutorial",
            "title",
            "page_number",
        )


class TutorialCreateSerializer(UserResourceSerializer[Tutorial]):
    scenarios = TutorialScenarioPageCreateSerializer(many=True)
    information_pages = TutorialInformationPageCreateSerializer(many=True)

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Tutorial
        fields = (
            "project",
            "is_draft",
        )

    # @typing.override
    # def create(self, validated_data: dict[typing.Any, typing.Any]):
    #     scenarios_data = validated_data.pop("scenarios")
    #     information_pages_data = validated_data.pop("information_pages")
    #     tutorial = Tutorial.objects.create(**validated_data)

    #     for scenario_data in scenarios_data:
    #         tasks_data = scenario_data.pop("tasks")
    #         scenario = TutorialScenarioPage.objects.create(**scenario_data)
    #         for task_data in tasks_data:
    #             task = TutorialTask.objects.create(**task_data)
    #             scenario.tasks.add(task)
    #         tutorial.scenarios.add(scenario)

    #     for information_page_data in information_pages_data:
    #         blocks_data = information_page_data.pop("blocks")
    #         information_page = TutorialInformationPage.objects.create(**information_page_data)
    #         for block_data in blocks_data:
    #             block = TutorialInformationPageBlock.objects.create(**block_data)
    #             information_page.blocks.add(block)
    #         tutorial.information_pages.add(information_page)

    #     return tutorial

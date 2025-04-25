import typing

import pydantic
from django.db import transaction
from django.utils.translation import gettext
from rest_framework import serializers

from apps.common.serializers import UserResourceSerializer
from apps.project.project_types.tile_map_service.compare import project as compare_project
from apps.project.project_types.tile_map_service.find import project as find_project
from utils.common import clean_up_none_keys
from utils.graphql.drf import handle_pydantic_validation_error

from .models import Project, ProjectAsset, ProjectTypeEnum
from .tasks import process_project_task

VALID_PROJECT_STATUS_TRANSITIONS = set(
    [
        (Project.Status.DRAFT, Project.Status.MARKED_AS_READY),
        (Project.Status.DRAFT, Project.Status.DISCARDED),
        (Project.Status.FAILED, Project.Status.MARKED_AS_READY),
        (Project.Status.FAILED, Project.Status.DISCARDED),
    ],
)

VALID_PROCESSED_PROJECT_STATUS_TRANSITIONS = set(
    [
        # NOTE: Transition from MARKED_AS_READY are updated by the system
        # (Project.Status.MARKED_AS_READY, Project.Status.FAILED),
        # (Project.Status.MARKED_AS_READY, Project.Status.READY),
        (Project.Status.READY, Project.Status.PUBLISHED),
        (Project.Status.READY, Project.Status.DISCARDED),
        (Project.Status.PUBLISHED, Project.Status.ARCHIVED),
        (Project.Status.PUBLISHED, Project.Status.PAUSED),
        (Project.Status.PUBLISHED, Project.Status.DISCARDED),
        (Project.Status.PAUSED, Project.Status.DISCARDED),
        (Project.Status.PAUSED, Project.Status.PUBLISHED),
    ],
)

PROJECT_TYPE_PROPERTY_MAP = {
    # FIXME(tnagorra): Handle completeness
    ProjectTypeEnum.COMPARE: ("compare", compare_project.CompareProjectProperty),
    ProjectTypeEnum.FIND: ("find", find_project.FindProjectProperty),
}


# NOTE: Make sure this matches with the strawberry Input ./graphql/inputs.py
class ProjectCreateSerializer(UserResourceSerializer[Project]):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Project
        fields = (
            "project_type",
            "requesting_organization",
            "name",
            "look_for",
            "additional_info_url",
            "description",
            "image",
        )


# NOTE: Make sure this matches with the strawberry Input ./graphql/inputs.py
class ProjectUpdateSerializer(UserResourceSerializer[Project]):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Project
        fields = (
            "project_type",
            "requesting_organization",
            "name",
            "look_for",
            "additional_info_url",
            "description",
            "image",
            "verification_number",
            "group_size",
            "max_tasks_per_user",
            "project_type_specifics",
            "status",
        )

    def validate_status(self, new_status: Project.Status):
        assert self.instance is not None

        if (self.instance.status, new_status) not in VALID_PROJECT_STATUS_TRANSITIONS:
            raise serializers.ValidationError(
                gettext("Project status cannot be changed from %s to %s") % (self.instance.status, new_status),
            )
        return new_status

    def _validate_project_type_specifics(self, attrs: dict[str, typing.Any]):
        assert self.instance is not None

        project_type = attrs.get("project_type") or self.instance.project_type_enum
        if project_type is None:
            raise serializers.ValidationError(
                {
                    "project_type": gettext("Project type is required."),
                },
            )

        project_type_label = ProjectTypeEnum.get_display(project_type)
        if project_type not in PROJECT_TYPE_PROPERTY_MAP:
            raise serializers.ValidationError(
                {
                    "project_type_specifics": gettext("Given project type is not handled: %s") % project_type_label,
                },
            )
        field_name, pydantic_model = PROJECT_TYPE_PROPERTY_MAP[project_type]

        raw_project_type_specifics = attrs.get("project_type_specifics")

        if raw_project_type_specifics is None and attrs.get("status") != Project.Status.MARKED_AS_READY:
            # NOTE: project_type_specifics is only required when project status is MARKED_AS_READY
            return

        if raw_project_type_specifics is not None:
            project_type_specifics = raw_project_type_specifics.get(field_name)
        else:
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
            pydantic_model.model_validate(project_type_specifics)
        except pydantic.ValidationError as pydantic_error:
            raise handle_pydantic_validation_error("project_type_specifics", pydantic_error) from None

        attrs["project_type_specifics"] = project_type_specifics

    @typing.override
    def validate(self, attrs: dict[str, typing.Any]):
        assert self.instance is not None

        if self.instance.status != Project.Status.DRAFT and self.instance.status != Project.Status.FAILED:
            raise serializers.ValidationError(gettext("Cannot update project with status %s") % self.instance.status)

        self._validate_project_type_specifics(attrs)
        return super().validate(attrs)

    @typing.override
    def update(self, instance: Project, validated_data: dict[str, typing.Any]) -> Project:
        new_project = super().update(instance, validated_data)

        user = self.context["request"].user

        if new_project.status == Project.Status.MARKED_AS_READY:
            transaction.on_commit(lambda: process_project_task.delay(new_project.pk, user.pk))

        return new_project


# NOTE: Make sure this matches with the strawberry Input ./graphql/inputs.py
class ProcessedProjectSerializer(UserResourceSerializer[Project]):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Project
        fields = (
            "requesting_organization",
            "name",
            "look_for",
            "additional_info_url",
            "description",
            "image",
            "status",
        )

    def validate_status(self, new_status: Project.Status):
        if not self.instance:
            raise Exception("Project does not exist")
        if (self.instance.status, new_status) not in VALID_PROCESSED_PROJECT_STATUS_TRANSITIONS:
            raise serializers.ValidationError(
                gettext("Project status cannot be changed from %s to %s") % (self.instance.status, new_status),
            )
        return new_status


# NOTE: Make sure this matches with the strawberry Input ./graphql/inputs.py
# FIXME(tnagorra): Should we validate the mimetype?
class ProjectAssetSerializer(UserResourceSerializer[ProjectAsset]):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = ProjectAsset
        fields = (
            "type",
            "mimetype",
            "file",
            "project",
        )

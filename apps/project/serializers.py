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

from .models import Project, ProjectTypeEnum
from .tasks import process_project_task

VALID_PROJECT_STATUS_TRANSITIONS = set(
    [
        (Project.Status.DRAFT, Project.Status.MARKED_AS_READY),
        (Project.Status.DRAFT, Project.Status.DISCARDED),
        (Project.Status.FAILED, Project.Status.MARKED_AS_READY),
        (Project.Status.FAILED, Project.Status.DISCARDED),
    ],
)

VALID_READY_PROJECT_STATUS_TRANSITIONS = set(
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


# NOTE: Make sure this matches with the strawberry Input ./graphql/inputs.py
class ProjectSerializer(UserResourceSerializer[Project]):
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
            "aoi_geometry_file",
            "status",
        )

    def validate_status(self, new_status: Project.Status):
        if not self.instance:
            if new_status != Project.Status.DRAFT:
                raise serializers.ValidationError(gettext("During project creation, project status should be Draft"))
        else:
            if (self.instance.status, new_status) not in VALID_PROJECT_STATUS_TRANSITIONS:
                raise serializers.ValidationError(
                    gettext("Project status cannot be changed from %s to %s") % (self.instance.status, new_status),
                )

    def _validate_editable(self):
        if self.instance and self.instance.status != Project.Status.DRAFT and self.instance.status != Project.Status.FAILED:
            raise serializers.ValidationError(gettext("Cannot update project with status %s") % self.instance.status)

    def _validate_project_type_specifics(self, attrs: dict[str, typing.Any]):
        project_type = attrs["project_type"]
        raw_project_type_specifics = attrs["project_type_specifics"]

        ENUM_FIELD_MAP = {
            # FIXME(tnagorra): Handle completeness
            ProjectTypeEnum.COMPARE: ("compare", compare_project.CompareProjectProperty),
            ProjectTypeEnum.FIND: ("find", find_project.FindProjectProperty),
        }

        project_type_label = ProjectTypeEnum.get_display(project_type)
        if project_type not in ENUM_FIELD_MAP:
            raise serializers.ValidationError(
                {
                    "project_type_specifics": gettext("Given project type is not handled: %s") % project_type_label,
                },
            )

        field_name, pydantic_model = ENUM_FIELD_MAP[project_type]

        project_type_specifics = raw_project_type_specifics.get(field_name)

        if project_type_specifics is None:
            raise serializers.ValidationError(
                {"project_type_specifics": gettext("Configuration not provided for: %s") % project_type_label},
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
        self._validate_editable()
        self._validate_project_type_specifics(attrs)
        return super().validate(attrs)

    @typing.override
    def update(self, instance: Project, validated_data: dict[str, typing.Any]) -> Project:
        new_project = super().update(instance, validated_data)

        if new_project.status == Project.Status.MARKED_AS_READY:
            transaction.on_commit(lambda: process_project_task.delay(new_project.pk))

        return new_project


# NOTE: Make sure this matches with the strawberry Input ./graphql/inputs.py
class ReadyProjectSerializer(UserResourceSerializer[Project]):
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
        if (self.instance.status, new_status) not in VALID_READY_PROJECT_STATUS_TRANSITIONS:
            raise serializers.ValidationError(
                gettext("Project status cannot be changed from %s to %s") % (self.instance.status, new_status),
            )

import typing

import pydantic
from django.db import transaction
from django.utils.translation import gettext
from rest_framework import serializers

from apps.common.serializers import UserResourceSerializer
from apps.project.project_types.tile_map_service.change_detection import project as change_detection_project
from apps.project.project_types.tile_map_service.classification import project as classification_project
from utils.common import clean_up_none_keys
from utils.graphql.drf import handle_pydantic_validation_error

from .models import Project, ProjectTypeEnum
from .tasks import load_project_geometry


# NOTE: Make sure this matches with the strawberry Input ./graphql/inputs.py
class ProjectSerializer(UserResourceSerializer):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Project
        fields = (
            "name",
            "project_type",
            "organization",
            "image",
            "geometry_file",
            "group_size",
            "verification_number",
            "look_for",
            "project_type_specifics",
        )

    def _validate_project_type_specifics(self, attrs: dict):
        project_type = attrs["project_type"]
        raw_project_type_specifics = attrs["project_type_specifics"]

        ENUM_FIELD_MAP = {
            ProjectTypeEnum.CHANGE_DETECTION: ("change_detection", change_detection_project.ChangeDetectionProjectProperty),
            ProjectTypeEnum.BUILD_AREA: ("classification", classification_project.ClassificationProjectProperty),
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
    def validate(self, attrs: dict):
        self._validate_project_type_specifics(attrs)
        return attrs

    @typing.override
    def create(self, validated_data: dict):
        new_project = super().create(validated_data)
        transaction.on_commit(lambda: load_project_geometry.delay(new_project.pk))
        return new_project

import typing

import pydantic
from django.db import transaction
from django.utils.translation import gettext
from rest_framework import serializers

from apps.common.serializers import UserResourceSerializer
from apps.project.project_types.tile_map_service.compare import project as compare_project
from apps.project.project_types.tile_map_service.completeness import project as completeness_project
from apps.project.project_types.tile_map_service.find import project as find_project
from apps.project.project_types.validate import project as validate_project
from utils.common import clean_up_none_keys
from utils.graphql.drf import handle_pydantic_validation_error

from .models import Organization, Project, ProjectAsset, ProjectTypeEnum
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


# FIXME(tnagorra): Move this to utils
def get_project_property(project_type: ProjectTypeEnum | None):
    if project_type is None:
        return None
    if project_type == ProjectTypeEnum.COMPARE:
        return ("compare", compare_project.CompareProjectProperty)
    if project_type == ProjectTypeEnum.FIND:
        return ("find", find_project.FindProjectProperty)
    if project_type == ProjectTypeEnum.VALIDATE:
        return ("validate", validate_project.ValidateProjectProperty)
    if project_type == ProjectTypeEnum.COMPLETENESS:
        return ("completeness", completeness_project.CompletenessProjectProperty)
    typing.assert_never(project_type)


# NOTE: Make sure this matches with the strawberry Input ./graphql/inputs.py
class ProjectCreateSerializer(UserResourceSerializer[Project]):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Project
        fields = (
            "client_id",
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
            "client_id",
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
            "tutorial",
        )

    def validate_status(self, new_status: Project.Status | None):
        assert self.instance is not None

        if new_status is None:
            return None

        if (self.instance.status, new_status) not in VALID_PROJECT_STATUS_TRANSITIONS:
            raise serializers.ValidationError(
                gettext("Project status cannot be changed from %s to %s") % (self.instance.status, new_status),
            )
        return new_status

    def validate_image(self, new_image: ProjectAsset | None):
        assert self.instance is not None

        if new_image is None:
            return None

        asset_exists = (
            ProjectAsset.usable_objects()
            .filter(
                id=new_image.pk,
                type=ProjectAsset.Type.INPUT,
                mimetype__in=[
                    ProjectAsset.Mimetype.IMAGE_GIF,
                    ProjectAsset.Mimetype.IMAGE_JPEG,
                    ProjectAsset.Mimetype.IMAGE_PNG,
                ],
                project_id=self.instance.pk,
            )
            .exists()
        )
        if not asset_exists:
            raise serializers.ValidationError(gettext("ProjectAsset is invalid or does not exist."))

        return new_image

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

        project_property = get_project_property(project_type)
        if project_property is None:
            raise serializers.ValidationError(
                {
                    "project_type_specifics": gettext("Given project type is not handled: %s") % project_type_label,
                },
            )

        field_name, pydantic_model = project_property
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
            pydantic_model.model_validate(
                project_type_specifics,
                context={"project_id": self.instance.pk},
            )
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

        if new_project.status == Project.Status.MARKED_AS_READY:
            transaction.on_commit(lambda: process_project_task.delay(new_project.pk))

        return new_project


# NOTE: Make sure this matches with the strawberry Input ./graphql/inputs.py
class ProcessedProjectSerializer(UserResourceSerializer[Project]):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Project
        fields = (
            "client_id",
            "requesting_organization",
            "name",
            "look_for",
            "additional_info_url",
            "description",
            "image",
            "status",
            "tutorial",
        )

    def validate_status(self, new_status: Project.Status | None):
        if not self.instance:
            raise Exception("Project does not exist")

        if new_status is None:
            return None

        if (self.instance.status, new_status) not in VALID_PROCESSED_PROJECT_STATUS_TRANSITIONS:
            raise serializers.ValidationError(
                gettext("Project status cannot be changed from %s to %s") % (self.instance.status, new_status),
            )
        return new_status

    def validate_image(self, new_image: ProjectAsset | None):
        assert self.instance is not None

        if new_image is None:
            return None

        asset_exists = (
            ProjectAsset.usable_objects()
            .filter(
                id=new_image.pk,
                type=ProjectAsset.Type.INPUT,
                mimetype__in=[
                    ProjectAsset.Mimetype.IMAGE_GIF,
                    ProjectAsset.Mimetype.IMAGE_JPEG,
                    ProjectAsset.Mimetype.IMAGE_PNG,
                ],
                project_id=self.instance.pk,
            )
            .exists()
        )
        if not asset_exists:
            raise serializers.ValidationError(gettext("ProjectAsset is invalid or does not exist."))

        return new_image

    def _validate_tutorial(self, attrs: dict[str, typing.Any]):
        assert self.instance is not None
        tutorial = attrs.get("tutorial") or self.instance.tutorial
        # FIXME: Add validation that tutorial and project types must match

        if tutorial is None and attrs.get("status") == Project.Status.PUBLISHED:
            raise serializers.ValidationError(
                {"tutorial": gettext("Tutorial is required before publishing a project.")},
            )

    @typing.override
    def validate(self, attrs: dict[str, typing.Any]):
        assert self.instance is not None

        self._validate_tutorial(attrs)
        return super().validate(attrs)


# NOTE: Make sure this matches with the strawberry Input ./graphql/inputs.py
# FIXME(tnagorra): Should we validate the mimetype during upload?
class ProjectAssetSerializer(UserResourceSerializer[ProjectAsset]):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = ProjectAsset
        fields = (
            "client_id",
            "mimetype",
            "file",
            "project",
        )

    @typing.override
    def create(self, validated_data: dict[str, typing.Any]) -> ProjectAsset:
        # NOTE: User should only bye able to create INPUT type project assets
        validated_data["type"] = ProjectAsset.Type.INPUT
        return super().create(validated_data)


class OrganizationCreateSerializer(UserResourceSerializer[Organization]):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Organization
        fields = (
            "client_id",
            "name",
        )

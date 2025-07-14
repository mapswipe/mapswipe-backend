import mimetypes
import typing

import pydantic
from django.db import transaction
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext
from rest_framework import serializers

from apps.common.models import FirebasePushStatusEnum
from apps.common.serializers import ArchivableResourceSerializer, UserResourceSerializer
from apps.contributor.models import ContributorTeam
from apps.project.firebase import push_organization_to_firebase
from apps.tutorial.models import Tutorial
from project_types.store import get_project_property
from utils.common import clean_up_none_keys
from utils.graphql.drf import handle_pydantic_validation_error

from .models import Organization, Project, ProjectAsset, ProjectTypeEnum
from .tasks import process_project_task, push_project_to_firebase

if typing.TYPE_CHECKING:
    from django.core.files.base import ContentFile

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
        (Project.Status.PAUSED, Project.Status.PUBLISHED),
    ],
)


# NOTE: Make sure this matches with the strawberry Input ./graphql/inputs.py
class ProjectCreateSerializer(UserResourceSerializer[Project]):
    requesting_organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.filter(is_archived=False),
        required=True,
    )

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Project
        fields = (
            "project_type",
            "topic",
            "region",
            "project_number",
            "requesting_organization",
            "look_for",
            "additional_info_url",
            "description",
            "image",
            "team",
        )

    def validate_team(self, team: ContributorTeam | None) -> ContributorTeam | None:
        if team and team.is_archived:
            raise serializers.ValidationError(
                gettext("Cannot use archived team on a project."),
            )
        return team


# NOTE: Make sure this matches with the strawberry Input ./graphql/inputs.py
class ProjectUpdateSerializer(UserResourceSerializer[Project]):
    requesting_organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.filter(is_archived=False),
        required=True,
    )

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Project
        fields = (
            "project_type",
            "topic",
            "region",
            "project_number",
            "requesting_organization",
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
            "team",
        )

    def validate_team(self, team: ContributorTeam | None) -> ContributorTeam | None:
        if team and team.is_archived:
            raise serializers.ValidationError(
                gettext("Cannot use archived team on a project."),
            )
        return team

    def validate_status(self, new_status: Project.Status | int) -> Project.Status:
        assert self.instance is not None, "Project does not exist."

        if not isinstance(new_status, Project.Status):
            new_status = Project.Status(new_status)

        if (
            self.instance.status_enum != new_status
            and (self.instance.status_enum, new_status) not in VALID_PROJECT_STATUS_TRANSITIONS
        ):
            raise serializers.ValidationError(
                gettext("Project status cannot be changed from %s to %s")
                % (
                    self.instance.status_enum.label,
                    new_status.label,
                ),
            )
        return new_status

    def validate_tutorial(self, tutorial: Tutorial | None) -> Tutorial | None:
        assert self.instance is not None
        current_tutorial = self.instance.tutorial

        if tutorial and tutorial != current_tutorial and tutorial.status_enum == Tutorial.Status.ARCHIVED:
            raise serializers.ValidationError(gettext("Cannot assign archived tutorial to the project."))

        # FIXME(susilnem): Check if we should use project_type or project_type_enum
        # NOTE: If tutorial is provided, project attached to the tutorial should match the current project type
        if tutorial and tutorial.project and tutorial.project.project_type != self.instance.project_type:
            raise serializers.ValidationError(
                {"tutorial": gettext("Tutorial project type does not match the project type.")},
            )
        return tutorial

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

        if self.instance.status_enum != Project.Status.DRAFT and self.instance.status_enum != Project.Status.FAILED:
            raise serializers.ValidationError(gettext("Cannot update project with status %s") % self.instance.status)

        self._validate_project_type_specifics(attrs)
        return super().validate(attrs)

    @typing.override
    def update(self, instance: Project, validated_data: dict[str, typing.Any]) -> Project:  # type: ignore[reportIncompatibleMethodOverride]
        old_status_enum = instance.status_enum
        new_project = super().update(instance, validated_data)

        if old_status_enum != Project.Status.MARKED_AS_READY and new_project.status_enum == Project.Status.MARKED_AS_READY:
            transaction.on_commit(lambda: process_project_task.delay(new_project.pk))

        return new_project


# NOTE: Make sure this matches with the strawberry Input ./graphql/inputs.py
class ProcessedProjectSerializer(UserResourceSerializer[Project]):
    requesting_organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.filter(is_archived=False),
        required=True,
    )

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Project
        fields = (
            "requesting_organization",
            "topic",
            "region",
            "project_number",
            "look_for",
            "additional_info_url",
            "description",
            "image",
            "status",
            "tutorial",
            "team",
        )

    def validate_team(self, team: ContributorTeam | None) -> ContributorTeam | None:
        if team and team.is_archived:
            raise serializers.ValidationError(
                gettext("Cannot use archived team on a project."),
            )
        return team

    def validate_status(self, new_status: Project.Status | int):
        assert self.instance is not None, "Project does not exist."

        if not isinstance(new_status, Project.Status):
            new_status = Project.Status(new_status)

        if (
            self.instance.status_enum != new_status
            and (self.instance.status_enum, new_status) not in VALID_PROCESSED_PROJECT_STATUS_TRANSITIONS
        ):
            raise serializers.ValidationError(
                gettext("Project status cannot be changed from %s to %s")
                % (self.instance.status_enum.label, new_status.label),
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

    # FIXME(susilnem): Can we instead use field level validation?
    def _validate_tutorial(self, attrs: dict[str, typing.Any]):
        assert self.instance is not None
        new_tutorial = attrs.get("tutorial")
        current_tutorial = self.instance.tutorial
        tutorial = new_tutorial or current_tutorial

        if tutorial is None and attrs.get("status") == Project.Status.PUBLISHED:
            raise serializers.ValidationError(
                {"tutorial": gettext("Tutorial is required before publishing a project.")},
            )

        # FIXME(susilnem): Check if we should use new_tutorial.status or new_status.status_enum
        if new_tutorial and new_tutorial != current_tutorial and new_tutorial.status_enum == Tutorial.Status.ARCHIVED:
            raise serializers.ValidationError(gettext("Cannot assign archived tutorial to the project."))

        # FIXME(susilnem): Check if we should use project_type or project_type_enum
        # NOTE: If tutorial is provided, project attached to the tutorial should match the current project type
        if tutorial and tutorial.project and tutorial.project.project_type != self.instance.project_type:
            raise serializers.ValidationError(
                {"tutorial": gettext("Tutorial project type does not match the project type.")},
            )

    @typing.override
    def validate(self, attrs: dict[str, typing.Any]):
        assert self.instance is not None

        self._validate_tutorial(attrs)
        return super().validate(attrs)

    @typing.override
    def update(self, instance: Project, validated_data: dict[str, typing.Any]) -> Project:
        old_status_enum = instance.status_enum
        new_project = super().update(instance, validated_data)

        if (
            old_status_enum != Project.Status.PUBLISHED and new_project.status_enum == Project.Status.PUBLISHED
        ) or old_status_enum == Project.Status.PUBLISHED:
            new_project.update_firebase_push_status(FirebasePushStatusEnum.PENDING)

            # FIXME: We can call this on batch later as well or handle error scenario
            transaction.on_commit(lambda: push_project_to_firebase.delay(new_project.pk))

        return new_project


# NOTE: Make sure this matches with the strawberry Input ./graphql/inputs.py
class ProjectAssetSerializer(UserResourceSerializer[ProjectAsset]):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = ProjectAsset
        fields = (
            "mimetype",
            "file",
            "project",
        )

    def _validate_file(self, attrs: dict[str, typing.Any]):
        file_content: ContentFile[bytes] = attrs["file"]
        file_size = file_content.size

        if file_size > ProjectAsset.MAX_FILE_SIZE:
            raise serializers.ValidationError(
                gettext("Filesize should be less than: %s. Current is: %s")
                % (
                    filesizeformat(ProjectAsset.MAX_FILE_SIZE),
                    filesizeformat(file_size),
                ),
            )

        # https://docs.python.org/3/library/mimetypes.html#mimetypes.guess_type
        mimetype, _ = mimetypes.guess_type(file_content.name)  # type: ignore[reportUnknownArgumentType]
        # TODO(susilnem): Use library like filemagic to determine mimetype instead?
        if mimetype is None:
            raise serializers.ValidationError(
                gettext("Could not determine mimetype of the file: %s") % file_content.name,
            )

        if not ProjectAsset.Mimetype.is_valid_mimetype(mimetype):
            raise serializers.ValidationError(
                gettext("File mimetype is not supported: %s") % mimetype,
            )

        attrs["mimetype"] = ProjectAsset.Mimetype.get_mimetype_by_label(mimetype)
        attrs["file_size"] = file_size

    @typing.override
    def validate(self, attrs: dict[str, typing.Any]):
        self._validate_file(attrs)
        return super().validate(attrs)

    @typing.override
    def create(self, validated_data: dict[str, typing.Any]) -> ProjectAsset:
        # NOTE: User should only be able to create INPUT type project assets
        validated_data["type"] = ProjectAsset.Type.INPUT
        return super().create(validated_data)


class OrganizationSerializer(UserResourceSerializer[Organization], ArchivableResourceSerializer[Organization]):  # type: ignore[reportIncompatibleVariableOverride]
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Organization
        fields = ("name", "description", "abbreviation")

    @typing.override
    def create(self, validated_data: dict[str, typing.Any]) -> Organization:
        organization = super().create(validated_data)
        transaction.on_commit(lambda: push_organization_to_firebase.delay(organization.pk))
        return organization

    @typing.override
    def update(self, instance: Organization, validated_data: dict[typing.Any, typing.Any]):
        organization = super().update(instance, validated_data)
        transaction.on_commit(lambda: push_organization_to_firebase.delay(organization.pk))
        return organization

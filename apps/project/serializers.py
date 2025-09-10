import json
import typing

import pydantic
from django.contrib.gis.geos import Point, Polygon
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext
from rest_framework import serializers

from apps.common.models import AssetMimetypeEnum, FirebasePushStatusEnum
from apps.common.serializers import ArchivableResourceSerializer, CommonAssetSerializer, UserResourceSerializer
from apps.contributor.models import ContributorTeam
from apps.project.firebase.push import FirebaseOrganizationPush
from apps.tutorial.models import Tutorial
from project_types.store import get_project_property, get_project_type_handler
from utils.asset_types.models import AoiGeometryAssetProperty, ObjectImageAssetProperty
from utils.common import clean_up_none_keys
from utils.geo.transform import convert_json_dict_to_geometry_collection
from utils.graphql.drf import handle_pydantic_validation_error

from .models import Geometry, Organization, Project, ProjectAsset, ProjectAssetInputTypeEnum, ProjectTypeEnum
from .tasks import process_project_task, push_project_to_firebase

if typing.TYPE_CHECKING:
    from django.core.files.base import ContentFile

VALID_PROJECT_STATUS_TRANSITIONS = set(
    [
        (Project.Status.DRAFT, Project.Status.READY_TO_PROCESS),
        (Project.Status.DRAFT, Project.Status.DISCARDED),
        (Project.Status.PROCESSING_FAILED, Project.Status.DISCARDED),
        (Project.Status.PROCESSING_FAILED, Project.Status.READY_TO_PROCESS),
        # (Project.Status.READY_TO_PROCESS, Project.Status.PROCESSING_FAILED),  # auto on bg
        # (Project.Status.READY_TO_PROCESS, Project.Status.PROCESSED),          # auto on bg
        (Project.Status.PROCESSED, Project.Status.READY_TO_PUBLISH),
        (Project.Status.PROCESSED, Project.Status.DISCARDED),
        (Project.Status.PUBLISHING_FAILED, Project.Status.DISCARDED),
        (Project.Status.PUBLISHING_FAILED, Project.Status.READY_TO_PUBLISH),
        # (Project.Status.READY_TO_PUBLISH, Project.Status.PUBLISHING_FAILED),  # auto on bg
        # (Project.Status.READY_TO_PUBLISH, Project.Status.PUBLISHED),          # auto on bg
        (Project.Status.PUBLISHED, Project.Status.WITHDRAWN),
        (Project.Status.PUBLISHED, Project.Status.FINISHED),
        (Project.Status.PUBLISHED, Project.Status.PAUSED),
        (Project.Status.PAUSED, Project.Status.PUBLISHED),
    ],
)


# NOTE: Make sure this matches with the strawberry Input ./graphql/inputs.py
class ProjectCreateSerializer(UserResourceSerializer[Project]):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Project
        fields = (
            "project_type",
            "topic",
            "region",
            "project_number",
            "requesting_organization",
            "look_for",
            "project_instruction",
            "additional_info_url",
            "description",
            "image",
            "team",
        )

    def validate_requesting_organization(self, requesting_organization: Organization | None) -> Organization | None:
        if requesting_organization and requesting_organization.is_archived:
            raise serializers.ValidationError(gettext("Cannot use archived organization on a project."))
        return requesting_organization

    def validate_team(self, team: ContributorTeam | None) -> ContributorTeam | None:
        if team and team.is_archived:
            raise serializers.ValidationError(gettext("Cannot use archived team on a project."))
        return team


# NOTE: Make sure this matches with the strawberry Input ./graphql/inputs.py
class ProjectUpdateSerializer(UserResourceSerializer[Project]):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Project
        fields = (
            "topic",
            "region",
            "project_number",
            "requesting_organization",
            "look_for",
            "project_instruction",
            "additional_info_url",
            "description",
            "image",
            "verification_number",
            "group_size",
            "max_tasks_per_user",
            "project_type_specifics",
            "tutorial",
            "team",
        )

    def validate_requesting_organization(self, requesting_organization: Organization | None) -> Organization | None:
        assert self.instance is not None
        current_org = self.instance.requesting_organization
        if requesting_organization and requesting_organization != current_org and requesting_organization.is_archived:
            raise serializers.ValidationError(gettext("Cannot use archived organization on a project."))
        return requesting_organization

    def validate_team(self, team: ContributorTeam | None) -> ContributorTeam | None:
        assert self.instance is not None
        current_team = self.instance.team
        if team and team != current_team and team.is_archived:
            raise serializers.ValidationError(gettext("Cannot use archived team on a project."))
        return team

    def validate_tutorial(self, tutorial: Tutorial | None) -> Tutorial | None:
        assert self.instance is not None
        current_tutorial = self.instance.tutorial
        if tutorial and tutorial != current_tutorial and tutorial.status_enum == Tutorial.Status.ARCHIVED:
            raise serializers.ValidationError(gettext("Cannot use archived tutorial on a project."))

        # NOTE: If tutorial is provided, project attached to the tutorial should match the current project type
        if tutorial and tutorial.project and tutorial.project.project_type_enum != self.instance.project_type_enum:
            raise serializers.ValidationError("Tutorial project type does not match the project type.")

        # FIXME(tnagorra): We should also check if the parameters are the same. eg. zoomLevel, ...
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
                input_type=ProjectAssetInputTypeEnum.COVER_IMAGE,
                project_id=self.instance.pk,
            )
            .exists()
        )
        if not asset_exists:
            raise serializers.ValidationError(gettext("ProjectAsset is invalid or does not exist."))

        return new_image

    def _validate_project_instruction(self, attrs: dict[str, typing.Any]):
        assert self.instance is not None
        # NOTE: project_instruction is not required in the database
        project_instruction = attrs.get("project_instruction") or self.instance.project_instruction
        if not project_instruction:
            raise serializers.ValidationError(
                {
                    "project_instruction": gettext("Project instruction is required."),
                },
            )

    def _validate_project_type_specifics(self, attrs: dict[str, typing.Any]):
        assert self.instance is not None

        project_type = self.instance.project_type_enum
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

        if raw_project_type_specifics is None and attrs.get("status") != Project.Status.READY_TO_PROCESS:
            # NOTE: project_type_specifics is only required when project status is READY_TO_PROCESS
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

        if self.instance.status_enum not in [Project.Status.DRAFT, Project.Status.PROCESSING_FAILED]:
            raise serializers.ValidationError(
                {
                    "status": gettext("Cannot update project with status %s") % self.instance.status_enum.label,
                },
            )

        self._validate_project_instruction(attrs)
        self._validate_project_type_specifics(attrs)
        return super().validate(attrs)

    @typing.override
    def update(self, instance: Project, validated_data: dict[typing.Any, typing.Any]):
        proj = super().update(instance, validated_data)

        # NOTE: We only need to attach aoi_geometry_input_asset if project_type_specifics is defined
        if proj.project_type_specifics:
            project_handler = get_project_type_handler(proj.project_type_enum)(proj)

            aoi_geom_asset = project_handler.get_aoi_geometry_asset()

            proj.aoi_geometry_input_asset = aoi_geom_asset

            if aoi_geom_asset:
                asset_specific_data = AoiGeometryAssetProperty.model_validate(aoi_geom_asset.asset_type_specifics)

                lng, lat = asset_specific_data.center
                centroid = Point(lng, lat)

                min_lng, min_lat, max_lng, max_lat = asset_specific_data.bbox
                bbox = Polygon(
                    (
                        (min_lng, min_lat),
                        (min_lng, max_lat),
                        (max_lng, max_lat),
                        (max_lng, min_lat),
                        (min_lng, min_lat),
                    ),
                )

                total_area = asset_specific_data.area

                try:
                    geojson_data = json.load(aoi_geom_asset.file)
                except json.JSONDecodeError as e:
                    raise serializers.ValidationError(
                        {
                            "file": "Invalid JSON format in the AOI file.",
                        },
                    ) from e

                try:
                    geometry_collection = convert_json_dict_to_geometry_collection(geojson_data)
                except Exception as e:
                    raise serializers.ValidationError(
                        {
                            "file": "Invalid AOI Feature Collection",
                        },
                    ) from e

                proj_aoi_geometry = proj.aoi_geometry
                if not proj_aoi_geometry:
                    aoi_geometry = Geometry(
                        bbox=bbox,
                        centroid=centroid,
                        geometry=geometry_collection,
                        total_area=total_area,
                    )
                    aoi_geometry.save()
                    proj.aoi_geometry = aoi_geometry
                else:
                    proj_aoi_geometry.bbox = bbox
                    proj_aoi_geometry.centroid = centroid
                    proj_aoi_geometry.geometry = geometry_collection
                    proj_aoi_geometry.total_area = total_area
                    proj_aoi_geometry.save()
            else:
                proj_aoi_geometry = proj.aoi_geometry
                if proj_aoi_geometry:
                    proj_aoi_geometry.delete()

            proj.save(update_fields=["aoi_geometry", "aoi_geometry_input_asset", "total_area"])

        return proj


# NOTE: Make sure this matches with the strawberry Input ./graphql/inputs.py
class ProcessedProjectSerializer(UserResourceSerializer[Project]):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Project
        fields = (
            "requesting_organization",
            "topic",
            "region",
            "project_number",
            "look_for",
            "project_instruction",
            "additional_info_url",
            "description",
            "image",
            "tutorial",
            "team",
            "is_featured",
        )

    def validate_requesting_organization(self, requesting_organization: Organization | None) -> Organization | None:
        assert self.instance is not None
        current_org = self.instance.requesting_organization
        if requesting_organization and requesting_organization != current_org and requesting_organization.is_archived:
            raise serializers.ValidationError(gettext("Cannot use archived organization on a project."))
        return requesting_organization

    def validate_team(self, team: ContributorTeam | None) -> ContributorTeam | None:
        assert self.instance is not None
        current_team = self.instance.team
        if team and team != current_team and team.is_archived:
            raise serializers.ValidationError(gettext("Cannot use archived team on a project."))
        return team

    def validate_tutorial(self, tutorial: Tutorial | None) -> Tutorial | None:
        assert self.instance is not None
        current_tutorial = self.instance.tutorial
        if tutorial and tutorial != current_tutorial and tutorial.status_enum == Tutorial.Status.ARCHIVED:
            raise serializers.ValidationError(gettext("Cannot use archived tutorial on a project."))

        # NOTE: If tutorial is provided, project attached to the tutorial should match the current project type
        if tutorial and tutorial.project and tutorial.project.project_type_enum != self.instance.project_type_enum:
            raise serializers.ValidationError(gettext("Tutorial project type does not match the project type."))

        # FIXME(tnagorra): We should also check if the parameters are the same. eg. zoomLevel, ...
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
                input_type=ProjectAssetInputTypeEnum.COVER_IMAGE,
                project_id=self.instance.pk,
            )
            .exists()
        )
        if not asset_exists:
            raise serializers.ValidationError(gettext("ProjectAsset is invalid or does not exist."))

        return new_image

    def _validate_project_instruction(self, attrs: dict[str, typing.Any]):
        assert self.instance is not None
        # NOTE: project_instruction is not required in the database
        project_instruction = attrs.get("project_instruction") or self.instance.project_instruction
        if not project_instruction:
            # FIXME: only validate on READY_TO_PROCESS
            raise serializers.ValidationError(
                {
                    "project_instruction": gettext("Project instruction is required."),
                },
            )

    @typing.override
    def validate(self, attrs: dict[str, typing.Any]):
        assert self.instance is not None

        # FIXME(tnagorra): Should we be able to edit paused, withdrawn, and published project
        if self.instance.status_enum not in [
            Project.Status.PROCESSED,
            Project.Status.PUBLISHED,
            Project.Status.PUBLISHING_FAILED,
        ]:
            raise serializers.ValidationError(
                {
                    "status": gettext("Cannot update project with status %s") % self.instance.status_enum.label,
                },
            )

        self._validate_project_instruction(attrs)
        return super().validate(attrs)

    @typing.override
    def update(self, instance: Project, validated_data: dict[str, typing.Any]) -> Project:
        old_status_enum = instance.status_enum
        updated_project = super().update(instance, validated_data)

        # FIXME(tnagorra): Should we be able to edit paused and withdrawn projects?
        if old_status_enum == Project.Status.PUBLISHED and updated_project.status_enum == Project.Status.PUBLISHED:
            updated_project.update_firebase_push_status(FirebasePushStatusEnum.PENDING)
            # FIXME(tnagorra): Published project should not set state to PUBLISHING_FAILED
            transaction.on_commit(lambda: push_project_to_firebase.delay(updated_project.pk))

        return updated_project


# NOTE: Make sure this matches with the strawberry Input ./graphql/inputs.py
class ProjectAssetSerializer(CommonAssetSerializer, UserResourceSerializer[ProjectAsset]):  # type: ignore[reportIncompatibleVariableOverride]
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = ProjectAsset
        fields = (
            "file",
            "input_type",
            "project",
            "external_url",
            "asset_type_specifics",
        )

    def _validate_aoi_geometry(
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

        if not mimetype or mimetype not in [AssetMimetypeEnum.JSON, AssetMimetypeEnum.GEOJSON, AssetMimetypeEnum.PLAINTEXT]:
            raise ValidationError(
                {
                    "file": "Mimetype is should either be a Text, JSON or GeoJSON",
                },
            )

        try:
            geojson_data = json.load(file)
        except json.JSONDecodeError as e:
            raise ValidationError(
                {
                    "file": "Invalid JSON format in the file.",
                },
            ) from e

        try:
            geometry_collection = convert_json_dict_to_geometry_collection(geojson_data)
        except Exception as e:
            raise ValidationError(
                {
                    "file": "Invalid feature collection",
                },
            ) from e

        polygons_count = geometry_collection.num_geom
        MAX_POLYGONS = 20
        if polygons_count > MAX_POLYGONS:
            raise ValidationError(
                {
                    "file": f"AOI should not have more than {MAX_POLYGONS} polygons",
                },
            )

        area_m2: float = geometry_collection.transform(6933, clone=True).area
        area_km2 = area_m2 / 1000_000
        # NOTE: Using zoom 14 to calculate max area using formulae: 5 * (4 ** (23 - zoom_level))
        # This area is almost equal to size of Peru
        MAX_AOI_GEOMETRY_AREA = 1310720
        if area_km2 > MAX_AOI_GEOMETRY_AREA:
            raise ValidationError(
                {
                    "file": f"Area for AOI Geometry must be less than {MAX_AOI_GEOMETRY_AREA} sq. km",
                },
            )

        center = geometry_collection.centroid

        asset_specifics = {
            "aoi_geometry": {
                "bbox": geometry_collection.extent,
                "center": center.coords,
                "area": area_km2,
            },
        }
        attrs["asset_type_specifics"] = asset_specifics
        attrs["mimetype"] = AssetMimetypeEnum.GEOJSON

    def _validate_cover_image(
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

    def _validate_object_image(
        self,
        attrs: dict[str, typing.Any],
        mimetype: AssetMimetypeEnum | None,
    ) -> None:
        file: ContentFile[bytes] | None = attrs.get("file")
        if not file:
            return

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

    def _validate_asset_type_specifics(
        self,
        attrs: dict[str, typing.Any],
        model: tuple[str, type[pydantic.BaseModel]] | None,
    ) -> None:
        if model is None:
            attrs["asset_type_specifics"] = {}
            return

        key, pydantic_model = model

        raw_asset_type_specifics = attrs["asset_type_specifics"].get(key)

        asset_type_specifics = clean_up_none_keys(raw_asset_type_specifics)

        try:
            pydantic_model.model_validate(
                asset_type_specifics,
                # FIXME(tnagorra): Do we need to add context?
                # context={"project_id": self.instance.pk},
            )
        except pydantic.ValidationError as pydantic_error:
            raise handle_pydantic_validation_error("asset_type_specifics", pydantic_error) from None

        attrs["asset_type_specifics"] = asset_type_specifics

    @typing.override
    def validate(self, attrs: dict[str, typing.Any]) -> dict[str, typing.Any]:
        attrs = super().validate(attrs)

        input_type = attrs.get("input_type")
        mimetype = attrs.get("mimetype")
        external_url = attrs.get("external_url")

        input_type_enum = ProjectAssetInputTypeEnum(input_type)
        mimetype_enum = AssetMimetypeEnum(mimetype) if mimetype else None

        match input_type_enum:
            case ProjectAssetInputTypeEnum.AOI_GEOMETRY:
                self._validate_aoi_geometry(attrs, mimetype_enum)
                self._validate_asset_type_specifics(attrs, ("aoi_geometry", AoiGeometryAssetProperty))
            case ProjectAssetInputTypeEnum.COVER_IMAGE:
                self._validate_cover_image(attrs, mimetype_enum)
                self._validate_asset_type_specifics(attrs, None)
            case ProjectAssetInputTypeEnum.OBJECT_IMAGE:
                self._validate_object_image(attrs, mimetype_enum)
                self._validate_asset_type_specifics(
                    attrs,
                    ("object_image", ObjectImageAssetProperty) if external_url else None,
                )
            case _:
                typing.assert_never(input_type_enum)

        return attrs


class OrganizationSerializer(UserResourceSerializer[Organization], ArchivableResourceSerializer[Organization]):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Organization
        fields = ("name", "description", "abbreviation")

    @typing.override
    def create(self, validated_data: dict[str, typing.Any]) -> Organization:
        organization = super().create(validated_data)
        FirebaseOrganizationPush(organization).trigger()
        return organization

    @typing.override
    def update(self, instance: Organization, validated_data: dict[typing.Any, typing.Any]):
        organization = super().update(instance, validated_data)
        FirebaseOrganizationPush(organization).trigger()
        return organization


class ProjectStatusUpdateSerializer(UserResourceSerializer[Project]):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Project
        fields = ("status",)

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

    @typing.override
    def validate(self, attrs: dict[str, typing.Any]):
        assert self.instance is not None

        new_status = attrs.get("status")
        if not isinstance(new_status, Project.Status):
            new_status = Project.Status(new_status)

        # NOTE: This check should technically never be called.
        if new_status == Project.Status.PUBLISHED and not self.instance.project_instruction:
            raise serializers.ValidationError(
                {
                    "project_instruction": gettext("Project instruction is required."),
                },
            )

        if new_status == Project.Status.READY_TO_PROCESS and not self.instance.project_type_specifics:
            raise serializers.ValidationError(
                {
                    "project_type_specifics": gettext("project_type_specifics is required when project status is %s")
                    % (new_status.label),
                },
            )
        if new_status == Project.Status.READY_TO_PUBLISH and not self.instance.tutorial:
            raise serializers.ValidationError(
                {
                    "tutorial": gettext("Tutorial is required before publishing a project."),
                },
            )
        return attrs

    @typing.override
    def update(self, instance: Project, validated_data: dict[str, typing.Any]) -> Project:
        old_status_enum = instance.status_enum
        updated_project = super().update(instance, validated_data)

        if (
            old_status_enum != Project.Status.READY_TO_PROCESS
            and updated_project.status_enum == Project.Status.READY_TO_PROCESS
        ):
            transaction.on_commit(lambda: process_project_task.delay(updated_project.pk))

        elif (
            old_status_enum != Project.Status.READY_TO_PUBLISH
            and updated_project.status_enum == Project.Status.READY_TO_PUBLISH
        ):
            updated_project.update_firebase_push_status(FirebasePushStatusEnum.PENDING)
            transaction.on_commit(lambda: push_project_to_firebase.delay(updated_project.pk))

        return updated_project

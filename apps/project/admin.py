import typing
from typing import Any, Literal

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from djangoql.admin import DjangoQLSearchMixin  # type: ignore[reportMissingTypeStubs]

from apps.common.admin import ArchivableResourceAdmin, FirebaseResourceAdmin, UserResourceAdmin

from .models import Geometry, Organization, Project, ProjectAsset


class IncludedInTeamFilter(admin.SimpleListFilter):
    title = _("Included in Team")
    parameter_name = "included_in_team"

    @typing.override
    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> list[tuple[Literal["yes", "no"], str]]:  # type: ignore[reportMissingTypeArgument]
        return [
            ("yes", "Yes"),
            ("no", "No"),
        ]

    @typing.override
    def queryset(self, request: HttpRequest, queryset: QuerySet[Any]) -> QuerySet[Any] | None:
        value = self.value()
        match value:
            case "yes":
                return queryset.filter(team__isnull=False)
            case "no":
                return queryset.filter(team__isnull=True)
            case _:
                return queryset


@admin.register(Organization)
class OrganizationAdmin(
    DjangoQLSearchMixin,
    ArchivableResourceAdmin,
    FirebaseResourceAdmin,
    UserResourceAdmin,
    admin.ModelAdmin,  # type: ignore[reportMissingTypeArgument]
):
    list_display = ("name", "abbreviation")
    search_fields = ("name", "abbreviation")
    ordering = ("name", "abbreviation")
    list_select_related = True


@admin.register(Geometry)
class GeometryAdmin(DjangoQLSearchMixin, admin.ModelAdmin[Geometry]):
    list_display = ("id",)
    search_fields = ("id",)


@admin.register(Project)
class ProjectAdmin(DjangoQLSearchMixin, FirebaseResourceAdmin, UserResourceAdmin, admin.ModelAdmin):  # type: ignore[reportMissingTypeArgument]
    list_display = (
        "generated_name",
        "requesting_organization",
        "project_type",
        "tutorial",
        "team",
        "is_private",
        "status",
        "processing_status",
        "progress",
    )
    readonly_fields = ("generate_name", "slack_progress_notifications", "slack_thread_ts")
    search_fields = ("topic", "region")
    ordering = ("topic", "region")
    list_filter = (
        IncludedInTeamFilter,
        # "requesting_organization",
        # "team",
        "project_type",
        "is_private",
        "status",
        "processing_status",
    )
    list_select_related = True
    autocomplete_fields = (
        "requesting_organization",
        "team",
        "tutorial",
        "image",
        "aoi_geometry_input_asset",
        "project_type_specific_output_asset",
        "aoi_geometry",
    )

    @typing.override
    def get_queryset(self, request: HttpRequest) -> QuerySet[Project]:
        return (
            super()
            .get_queryset(request)
            .annotate(
                generated_name=Project.generate_name_query(),
            )
        )

    @admin.display(ordering="generated_name", description="Generated Name")
    def generated_name(self, obj: Project):
        return obj.generated_name  # type: ignore[reportAttributeAccessIssue]


@admin.register(ProjectAsset)
class ProjectAssetAdmin(DjangoQLSearchMixin, UserResourceAdmin, admin.ModelAdmin):  # type: ignore[reportMissingTypeArgument]
    list_display = ("project", "mimetype", "type", "input_type", "export_type", "file_size", "marked_as_deleted")
    list_filter = (
        # "project",
        "mimetype",
        "type",
        "input_type",
        "export_type",
    )
    list_select_related = True
    autocomplete_fields = ("project",)

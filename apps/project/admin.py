import typing
from typing import Any, Literal

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from djangoql.admin import DjangoQLSearchMixin

from apps.common.admin import ArchivableResourceAdmin, FirebaseResourceAdmin, ReadOnlyAdmin

from .models import Organization, Project, ProjectAsset


class IncludedInTeamFilter(admin.SimpleListFilter):
    title = _("Included in Team")
    parameter_name = "included_in_team"

    @typing.override
    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> list[tuple[Literal["yes", "no"], str]]:
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
    ReadOnlyAdmin,
    admin.ModelAdmin,
):
    list_display = ("name",)
    list_filter = ("name",)


@admin.register(Project)
class ProjectAdmin(DjangoQLSearchMixin, FirebaseResourceAdmin, ReadOnlyAdmin, admin.ModelAdmin):
    list_display = ("topic", "requesting_organization", "project_type", "is_private", "region")
    list_filter = (IncludedInTeamFilter, "topic", "project_type", "is_private", "region")
    list_select_related = True
    autocomplete_fields = ("requesting_organization", "tutorial", "image", "created_by", "team")


@admin.register(ProjectAsset)
class ProjectAssetAdmin(DjangoQLSearchMixin, ReadOnlyAdmin, admin.ModelAdmin):
    pass

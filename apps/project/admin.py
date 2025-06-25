import typing
from typing import Any, Literal

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from djangoql.admin import DjangoQLSearchMixin

from .models import Organization, Project, ProjectAsset


class HasTeamFilter(admin.SimpleListFilter):
    title = _("Has Team")
    parameter_name = "has_team"

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
class OrganizationAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    pass


@admin.register(Project)
class ProjectAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = ("name", "is_private")
    list_filter = (HasTeamFilter, "is_private")
    list_select_related = ("team",)


@admin.register(ProjectAsset)
class ProjectAssetAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    pass

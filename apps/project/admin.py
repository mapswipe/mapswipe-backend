from django.contrib import admin
from djangoql.admin import DjangoQLSearchMixin

from .models import Organization, Project, ProjectAsset


@admin.register(Organization)
class OrganizationAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = ("name",)
    list_filter = ("name",)


@admin.register(Project)
class ProjectAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = ("name", "requesting_organization", "project_type")
    list_filter = ("name", "project_type")
    list_select_related = True
    autocomplete_fields = ("requesting_organization", "tutorial", "image", "created_by")


@admin.register(ProjectAsset)
class ProjectAssetAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    pass

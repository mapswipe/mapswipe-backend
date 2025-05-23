from django.contrib import admin
from djangoql.admin import DjangoQLSearchMixin

from .models import Organization, Project, ProjectAsset


@admin.register(Organization)
class OrganizationAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    pass


@admin.register(Project)
class ProjectAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    pass


@admin.register(ProjectAsset)
class ProjectAssetAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    pass

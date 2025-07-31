from django.contrib import admin
from djangoql.admin import DjangoQLSearchMixin

from .models import Tutorial, TutorialAsset


@admin.register(Tutorial)
class TutorialAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = ("name", "project", "status")
    list_filter = ("status",)
    list_select_related = True
    autocomplete_fields = ("project", "created_by")


@admin.register(TutorialAsset)
class ProjectAssetAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    pass

from django.contrib import admin
from djangoql.admin import DjangoQLSearchMixin  # type: ignore[reportMissingTypeStubs]

from apps.common.admin import UserResourceAdmin

from .models import Tutorial, TutorialAsset


@admin.register(Tutorial)
class TutorialAdmin(DjangoQLSearchMixin, UserResourceAdmin, admin.ModelAdmin):  # type: ignore[reportMissingTypeArgument]
    list_display = ("name", "project", "status")
    search_fields = ("name",)
    ordering = ("name",)
    list_filter = (
        # "project",
        "status",
    )
    list_select_related = True
    autocomplete_fields = ("project",)


@admin.register(TutorialAsset)
class TutorialAssetAdmin(DjangoQLSearchMixin, UserResourceAdmin, admin.ModelAdmin):  # type: ignore[reportMissingTypeArgument]
    list_display = ("tutorial", "mimetype", "type", "input_type", "file_size", "marked_as_deleted")
    list_filter = (
        # "tutorial",
        "mimetype",
        "type",
        "input_type",
    )
    list_select_related = True
    autocomplete_fields = ("tutorial",)

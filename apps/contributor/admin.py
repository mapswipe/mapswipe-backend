from django.contrib import admin
from djangoql.admin import DjangoQLSearchMixin

from .models import ContributorTeam, ContributorUser, ContributorUserGroup


@admin.register(ContributorUser)
class ContributorUserAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = (
        "user_id",
        "username",
    )
    list_filter = ("team",)


@admin.register(ContributorUserGroup)
class ContributorUserGroupAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    pass


@admin.register(ContributorTeam)
class ContributorTeamAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = ("name", "is_archived")
    list_filter = ("is_archived",)

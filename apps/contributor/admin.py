from django.contrib import admin
from djangoql.admin import DjangoQLSearchMixin

from apps.common.admin import ArchivableResourceAdmin

from .models import ContributorTeam, ContributorUser, ContributorUserGroup, ContributorUserGroupMembership


@admin.register(ContributorUser)
class ContributorUserAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = (
        "user_id",
        "username",
        "created_at",
        "modified_at",
    )
    list_filter = ("team",)


@admin.register(ContributorUserGroup)
class ContributorUserGroupAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    pass


class ContributorUserInline(admin.TabularInline):
    model = ContributorUser
    extra = 1
    fields = ("user_id", "username", "created_at", "modified_at")
    can_delete = False


@admin.register(ContributorTeam)
class ContributorTeamAdmin(ArchivableResourceAdmin, DjangoQLSearchMixin, admin.ModelAdmin):
    inlines = [ContributorUserInline]
    list_display = (
        "name",
        "is_archived",
        "created_at",
        "modified_at",
    )
    list_filter = ("is_archived",)


@admin.register(ContributorUserGroupMembership)
class ContributorUserGroupMembershipAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = (
        "user",
        "user_group",
        "is_active",
    )

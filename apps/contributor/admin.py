import typing

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from djangoql.admin import DjangoQLSearchMixin

from apps.common.admin import ArchivableResourceAdmin, FirebaseResourceAdmin, UserResourceAdmin

from .firebase.push import FirebaseContributorTeam, FirebaseContributorUser
from .models import ContributorTeam, ContributorUser, ContributorUserGroup, ContributorUserGroupMembership


@admin.register(ContributorUser)
class ContributorUserAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    readonly_fields = (
        "firebase_id",
        "old_id",
        "username",
        "firebase_last_pushed",
        "firebase_push_status",
        "created_at",
        "modified_at",
    )
    list_display = ("firebase_id", "username", "team", "created_at")
    ordering = ("username", "team", "created_at")
    search_fields = ("username",)
    # list_filter = ("team",)
    list_select_related = True
    autocomplete_fields = ("team",)

    @typing.override
    def has_add_permission(self, *args, **kwargs):
        return False

    @typing.override
    def has_delete_permission(self, *args, **kwargs):
        return False

    @typing.override
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        FirebaseContributorUser(obj).trigger()


@admin.register(ContributorUserGroup)
class ContributorUserGroupAdmin(
    DjangoQLSearchMixin,
    ArchivableResourceAdmin,
    FirebaseResourceAdmin,
    UserResourceAdmin,
    admin.ModelAdmin,
):
    list_display = ("name",)
    ordering = ("name",)
    search_fields = ("name",)
    list_select_related = True


@admin.register(ContributorTeam)
class ContributorTeamAdmin(
    DjangoQLSearchMixin,
    ArchivableResourceAdmin,
    FirebaseResourceAdmin,
    UserResourceAdmin,
    admin.ModelAdmin,
):
    list_display = ("name", "view_team_members")
    ordering = ("name",)
    search_fields = ("name",)
    list_select_related = True

    @typing.override
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        FirebaseContributorTeam(obj).trigger()

    def view_team_members(self, obj):
        url = reverse("admin:contributor_contributoruser_changelist") + f"?team__id__exact={obj.id}"
        return format_html('<a href="{}">View Team Members</a>', url)


@admin.register(ContributorUserGroupMembership)
class ContributorUserGroupMembershipAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = ("user", "user_group", "is_active")
    list_filter = (
        # "user",
        # "user_group",
        "is_active",
    )
    list_select_related = True
    autocomplete_fields = ("user", "user_group")

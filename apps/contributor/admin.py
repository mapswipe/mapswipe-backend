import typing

from django.contrib import admin
from django.db import transaction
from django.urls import reverse
from django.utils.html import format_html
from djangoql.admin import DjangoQLSearchMixin

from apps.common.admin import ArchivableResourceAdmin

from .firebase import FirebaseContributorTeam, firebase_contributor_user
from .models import ContributorTeam, ContributorUser, ContributorUserGroup, ContributorUserGroupMembership


@admin.register(ContributorUser)
class ContributorUserAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = (
        "firebase_id",
        "username",
        "created_at",
        "modified_at",
    )
    readonly_fields = (
        "firebase_id",
        "old_id",
        "username",
        "firebase_last_pushed",
        "firebase_push_status",
        "created_at",
        "modified_at",
    )
    list_filter = ("team",)

    @typing.override
    def has_add_permission(self, *args, **kwargs):
        return False

    @typing.override
    def has_delete_permission(self, *args, **kwargs):
        return False

    @typing.override
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)  # type: ignore[reportAttributeAccessIssue]
        transaction.on_commit(lambda: firebase_contributor_user.delay(obj.id))


@admin.register(ContributorUserGroup)
class ContributorUserGroupAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    pass


@admin.register(ContributorTeam)
class ContributorTeamAdmin(ArchivableResourceAdmin, DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = (
        "name",
        "is_archived",
        "created_at",
        "modified_at",
        "view_team_members",
    )
    list_filter = ("is_archived",)

    @typing.override
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)  # type: ignore[reportAttributeAccessIssue]
        transaction.on_commit(lambda: FirebaseContributorTeam.task.delay(obj.id))

    def view_team_members(self, obj):
        url = reverse("admin:contributor_contributoruser_changelist") + f"?team__id__exact={obj.id}"
        return format_html('<a href="{}">View Team Members</a>', url)


@admin.register(ContributorUserGroupMembership)
class ContributorUserGroupMembershipAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = (
        "user",
        "user_group",
        "is_active",
    )

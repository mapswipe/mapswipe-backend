import typing
from datetime import datetime

from django.contrib import admin
from django.db import transaction
from djangoql.admin import DjangoQLSearchMixin

from apps.common.admin import ArchivableResourceAdmin

from .models import ContributorTeam, ContributorUser, ContributorUserGroup, ContributorUserGroupMembership
from apps.contributor.firebase import push_contributor_team_to_firebase



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

    @typing.override
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        if obj.is_archived:
            obj.archived_by = request.user
            obj.archived_at = datetime.now()
        else:
            obj.archived_by = None
            obj.archived_at = None
        super().save_model(request, obj, form, change)  # type: ignore[reportAttributeAccessIssue]
        transaction.on_commit(lambda: push_contributor_team_to_firebase.delay(obj.pk))


@admin.register(ContributorUserGroupMembership)
class ContributorUserGroupMembershipAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = (
        "user",
        "user_group",
        "is_active",
    )

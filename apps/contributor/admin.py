import typing
from datetime import datetime

from django.contrib import admin
from django.db import transaction
from djangoql.admin import DjangoQLSearchMixin

from apps.common.admin import ArchivableResourceAdmin

from .firebase import FirebaseContributorTeam, firebase_contributor_user
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
        transaction.on_commit(lambda: FirebaseContributorTeam.task.delay(obj.id))

    @typing.override
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        contributor_users = form.instance.user.all()
        for user in contributor_users:
            transaction.on_commit(lambda user_id=user.pk: firebase_contributor_user.delay(user_id))


@admin.register(ContributorUserGroupMembership)
class ContributorUserGroupMembershipAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = (
        "user",
        "user_group",
        "is_active",
    )

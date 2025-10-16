import typing

from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin
from django.db import models
from django.db.models.functions import Coalesce
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import format_html
from djangoql.admin import DjangoQLSearchMixin  # type: ignore[reportMissingTypeStubs]

from apps.common.admin import ArchivableResourceAdmin, FirebaseResourceAdmin, UserResourceAdmin

from .firebase.push import FirebaseContributorTeam, FirebaseContributorUser
from .models import ContributorTeam, ContributorUser, ContributorUserGroup, ContributorUserGroupMembership


@admin.register(ContributorUser)
class ContributorUserAdmin(DjangoQLSearchMixin, admin.ModelAdmin):  # type: ignore[reportMissingTypeArgument]
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
    list_filter = (
        AutocompleteFilterFactory("Team", "team"),
        "created_at",
    )
    ordering = ("username", "team", "created_at")
    search_fields = ("username",)
    list_select_related = True
    autocomplete_fields = ("team",)

    @typing.override
    def has_add_permission(self, *args, **kwargs):  # type: ignore[reportMissingParameterType]
        return False

    @typing.override
    def has_delete_permission(self, *args, **kwargs):  # type: ignore[reportMissingParameterType]
        return False

    @typing.override
    def save_model(self, request, obj, form, change):  # type: ignore[reportMissingParameterType]
        super().save_model(request, obj, form, change)
        FirebaseContributorUser(obj).trigger()


@admin.register(ContributorUserGroup)
class ContributorUserGroupAdmin(
    DjangoQLSearchMixin,
    ArchivableResourceAdmin,
    FirebaseResourceAdmin,
    UserResourceAdmin,
    admin.ModelAdmin,  # type: ignore[reportMissingTypeArgument]
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
    admin.ModelAdmin,  # type: ignore[reportMissingTypeArgument]
):
    list_display = (
        "name",
        "members_count",
    )
    ordering = ("name",)
    search_fields = ("name",)
    list_select_related = True

    @typing.override
    def get_queryset(self, request: HttpRequest) -> models.QuerySet[ContributorTeam]:
        return (
            super()
            .get_queryset(request)
            .annotate(
                members_count=Coalesce(
                    models.Subquery(
                        ContributorUser.objects.filter(
                            team=models.OuterRef("id"),
                        )
                        .order_by()
                        .values("team")
                        .annotate(c=models.Count("id"))
                        .values("c")[:1],
                        output_field=models.IntegerField(),
                    ),
                    0,
                ),
            )
        )

    @typing.override
    def save_model(self, request, obj, form, change):  # type: ignore[reportMissingParameterType]
        super().save_model(request, obj, form, change)
        FirebaseContributorTeam(obj).trigger()

    @admin.display(ordering="members_count", description="Members count")
    def members_count(self, obj: ContributorTeam):
        url = reverse("admin:contributor_contributoruser_changelist") + f"?team={obj.id}"
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.members_count,  # type: ignore[reportAttributeAccessIssue]
        )


@admin.register(ContributorUserGroupMembership)
class ContributorUserGroupMembershipAdmin(DjangoQLSearchMixin, admin.ModelAdmin):  # type: ignore[reportMissingTypeArgument]
    list_display = ("user", "user_group", "is_active")
    list_filter = (
        # "user",
        # "user_group",
        "is_active",
    )
    list_select_related = True
    autocomplete_fields = ("user", "user_group")

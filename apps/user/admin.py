import typing

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from .models import User


class UserCreationForm(forms.ModelForm):  # type: ignore[reportMissingTypeArgument]
    class Meta:
        model = User
        fields = ["email"]


class HasSlackUserIdFilter(admin.SimpleListFilter):
    title = _("Slack User ID")
    parameter_name = "has_slack_user_id"

    @typing.override
    def lookups(self, request, model_admin):
        return (
            ("yes", gettext("Has value")),
            ("no", gettext("Is empty")),
        )

    @typing.override
    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.exclude(slack_user_id__isnull=True).exclude(slack_user_id__exact="")
        if self.value() == "no":
            return queryset.filter(slack_user_id__isnull=True) | queryset.filter(slack_user_id__exact="")
        return queryset


@admin.register(User)
class UserAdmin(DjangoUserAdmin):  # type: ignore[reportMissingTypeArgument]
    list_display = (
        "email",
        "first_name",
        "last_name",
        "slack_user_id",
        "contributor_user__firebase_id",
        "contributor_user__username",
        "is_active",
        "is_staff",
        "is_superuser",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "groups",
        HasSlackUserIdFilter,
    )
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email", "first_name", "last_name")
    add_form = UserCreationForm
    readonly_fields = ("display_name",)
    autocomplete_fields = ("contributor_user",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "password",
                ),
            },
        ),
        (
            _("Personal info"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "display_name",
                    "contributor_user",
                    "slack_user_id",
                ),
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email",),
            },
        ),
    )

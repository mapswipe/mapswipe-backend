from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.common.admin import ReadOnlyAdmin

from .models import User


class UserCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email"]


@admin.register(User)
class UserAdmin(DjangoUserAdmin, ReadOnlyAdmin):
    list_display = (
        "email",
        "contributor_user__firebase_id",
        "contributor_user__username",
        "first_name",
        "last_name",
        "is_staff",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("first_name", "last_name", "email")
    ordering = ("email",)
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

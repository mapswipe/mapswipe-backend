import typing
from datetime import datetime

from django.contrib import admin
from django.db import models
from django.http import HttpRequest

from apps.common.models import UserResource

DjangoModel = typing.TypeVar("DjangoModel", bound=models.Model)


# FIXME(tnagorra): Do we use Mixin or extend admin.ModelAdmin
# TODO(tnagorra): Use readonly mixin
class ReadOnlyMixin:
    def has_add_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False


class UserResourceAdmin(admin.ModelAdmin):
    @typing.override
    def get_readonly_fields(self, *args, **kwargs):
        readonly_fields = super().get_readonly_fields(*args, **kwargs)  # type: ignore[reportAttributeAccessIssue]
        return [
            # To maintain order
            *dict.fromkeys(
                [
                    *readonly_fields,
                    "created_at",
                    "created_by",
                    "modified_at",
                    "modified_by",
                ],
            ),
        ]

    @typing.override
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)  # type: ignore[reportAttributeAccessIssue]

    @typing.override
    def save_formset(self, request, form, formset, change) -> None:
        if not issubclass(formset.model, UserResource):
            return super().save_formset(request, form, formset, change)
        # https://docs.djangoproject.com/en/4.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.save_formset
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for instance in instances:
            # UserResource changes
            if instance.pk is None:
                instance.created_by = request.user
            instance.modified_by = request.user
            instance.save()
        return None

    @typing.override
    def get_queryset(self, request: HttpRequest) -> models.QuerySet[DjangoModel]:
        return super().get_queryset(request).select_related("created_by", "modified_by")


class ArchivableResourceAdmin(UserResourceAdmin, admin.ModelAdmin):
    @typing.override
    def get_readonly_fields(self, *args, **kwargs):
        readonly_fields = super().get_readonly_fields(*args, **kwargs)  # type: ignore[reportAttributeAccessIssue]
        return [
            *dict.fromkeys(
                [
                    *readonly_fields,
                    "archived_by",
                    "archived_at",
                ],
            ),
        ]

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


class FirebaseResourceAdmin(UserResourceAdmin, admin.ModelAdmin):
    @typing.override
    def get_readonly_fields(self, *args, **kwargs):
        readonly_fields = super().get_readonly_fields(*args, **kwargs)  # type: ignore[reportAttributeAccessIssue]
        return [
            *dict.fromkeys(
                [
                    *readonly_fields,
                    "firebase_id",
                    "firebase_last_pushed",
                    "firebase_push_status",
                ],
            ),
        ]

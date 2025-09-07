import typing
from datetime import datetime

from django.contrib import admin
from django.db import models
from django.http import HttpRequest
from djangoql.admin import DjangoQLSearchMixin

from apps.common.firebase.push import FirebaseAnnouncementPush
from apps.common.models import Announcement, GlobalExportAsset, UserResource

DjangoModel = typing.TypeVar("DjangoModel", bound=models.Model)


class UserResourceAdmin(admin.ModelAdmin):
    @typing.override
    def get_autocomplete_fields(self, *args, **kwargs):
        autocomplete_fields = super().get_autocomplete_fields(*args, **kwargs)
        return [
            *dict.fromkeys(
                [
                    *autocomplete_fields,
                    "created_by",
                    "modified_by",
                ],
            ),
        ]

    @typing.override
    def get_readonly_fields(self, *args, **kwargs):
        readonly_fields = super().get_readonly_fields(*args, **kwargs)
        return [
            # To maintain order
            *dict.fromkeys(
                [
                    *readonly_fields,
                    "created_at",
                    "modified_at",
                    # "created_by",
                    # "modified_by",
                ],
            ),
        ]

    @typing.override
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)

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


class ArchivableResourceAdmin(admin.ModelAdmin):
    @typing.override
    def get_list_display(self, *args, **kwargs):
        list_display = super().get_list_display(*args, **kwargs)
        return [
            *dict.fromkeys(
                [
                    *list_display,
                    "is_archived",
                ],
            ),
        ]

    @typing.override
    def get_list_filter(self, *args, **kwargs):
        list_filter = super().get_list_filter(*args, **kwargs)
        return [
            *dict.fromkeys(
                [
                    *list_filter,
                    "is_archived",
                ],
            ),
        ]

    @typing.override
    def get_autocomplete_fields(self, *args, **kwargs):
        autocomplete_fields = super().get_autocomplete_fields(*args, **kwargs)
        return [
            *dict.fromkeys(
                [
                    *autocomplete_fields,
                    "archived_by",
                ],
            ),
        ]

    @typing.override
    def get_readonly_fields(self, *args, **kwargs):
        readonly_fields = super().get_readonly_fields(*args, **kwargs)
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
        super().save_model(request, obj, form, change)


class FirebaseResourceAdmin(admin.ModelAdmin):
    # FIXME(tnagorra): Add ordering for firebase_last_pushed

    @typing.override
    def get_list_display(self, *args, **kwargs):
        list_display = super().get_list_display(*args, **kwargs)
        return [
            *dict.fromkeys(
                [
                    "firebase_id",
                    *list_display,
                    "firebase_last_pushed",
                    "firebase_push_status",
                ],
            ),
        ]

    @typing.override
    def get_list_filter(self, *args, **kwargs):
        list_filter = super().get_list_filter(*args, **kwargs)
        return [
            *dict.fromkeys(
                [
                    *list_filter,
                    "firebase_push_status",
                ],
            ),
        ]

    @typing.override
    def get_readonly_fields(self, *args, **kwargs):
        readonly_fields = super().get_readonly_fields(*args, **kwargs)
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


@admin.register(GlobalExportAsset)
class GlobalExportAssetAdmin(DjangoQLSearchMixin, admin.ModelAdmin[GlobalExportAsset]):
    list_display = ("type", "file_size", "file", "last_updated_at")


@admin.register(Announcement)
class AnnouncementAdmin(DjangoQLSearchMixin, FirebaseResourceAdmin, UserResourceAdmin, admin.ModelAdmin):
    list_display = ("text", "is_active", "url")

    @typing.override
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if obj.is_active:
            previous_announcements = Announcement.objects.exclude(id=obj.id)
            previous_announcements.update(is_active=False)

            FirebaseAnnouncementPush(obj).trigger()
        else:
            FirebaseAnnouncementPush(obj).trigger(delete=True)

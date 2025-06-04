from django.contrib import admin
from djangoql.admin import DjangoQLSearchMixin

from .models import ContributorUserGroup


@admin.register(ContributorUserGroup)
class ContributorUserGroupAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    pass

from django.contrib import admin
from djangoql.admin import DjangoQLSearchMixin

from .models import Tutorial


@admin.register(Tutorial)
class TutorialAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    pass

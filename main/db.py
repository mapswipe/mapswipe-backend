from django.db import models
from django_cte import CTEManager  # type: ignore[reportMissingTypeStubs]

from main.config import Config


class Model(models.Model):
    cte_objects = CTEManager()
    objects = models.Manager()

    class Meta:
        abstract = True


class ExistingDatabaseRouter:
    route_app_labels = {"existing_database"}

    def db_for_read(self, model, **hints):  # type: ignore[reportMissingParameterType]
        if model._meta.app_label in self.route_app_labels:
            return Config.EXISTING_SYSTEM_POSTGRES_KEY
        return None

    def db_for_write(self, model, **hints):  # type: ignore[reportMissingParameterType]
        if model._meta.app_label in self.route_app_labels:
            return Config.EXISTING_SYSTEM_POSTGRES_KEY
        return None

    def allow_relation(self, obj1, obj2, **hints):  # type: ignore[reportMissingParameterType]
        return obj1._state.db == obj2._state.db

    def allow_migrate(self, db, app_label, model_name=None, **hints):  # type: ignore[reportMissingParameterType]
        return app_label not in self.route_app_labels

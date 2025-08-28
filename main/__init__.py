import django_stubs_ext

from .celery import app as celery_app

__all__ = ("celery_app",)

django_stubs_ext.monkeypatch()

import typing

from django.apps import AppConfig


class ProjectConfig(AppConfig):
    name = "apps.project"

    @typing.override
    def ready(self) -> None:
        from . import signals  # noqa: F401, PLC0415  # pyright: ignore[reportUnusedImport]

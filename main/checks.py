from pydoc import locate

from django.conf import settings
from django.core.checks import Error, Info, Tags, register
from django.core.checks import Warning as DCWarning


@register(Tags.compatibility)
def celery_beat_tasks(app_configs, **kwargs):  # type: ignore[reportMissingParameterType]
    from main.cronjobs import SCHEDULES

    # Confirm all tasks can be imported
    errors = []
    for name, config in SCHEDULES.items():
        if locate(config.task) is None:
            errors.append(Error(f"Celery beat <{name}> task is incorrect: {config.task}"))

    return errors


@register(Tags.compatibility)
def firebase_check(app_configs, **kwargs):  # type: ignore[reportMissingParameterType]
    if not settings.FIREBASE_EMULATOR_USE:
        return []

    # For local debugging
    return [
        DCWarning("FIREBASE_EMULATOR_USE is enabled"),
        Info(f"databaseUrl is {settings.FIREBASE_DB_URL}"),
        Info(f"Firebase credential is included: {settings.FIREBASE_CREDENTIALS_B64_GZ is not None}"),
    ]

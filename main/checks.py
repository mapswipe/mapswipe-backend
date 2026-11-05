from pydoc import locate

from django.conf import settings
from django.core.checks import Error, Info, Tags, register
from django.core.checks import Warning as DCWarning

from main.storage_config import DEFAULT_STORAGE_KEY, SHORT_TERM_STORAGE_KEY, get_storage_target


@register(Tags.compatibility)
def celery_beat_tasks(app_configs, **kwargs):  # type: ignore[reportMissingParameterType]
    from main.cronjobs import SCHEDULES  # noqa: PLC0415

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


@register(Tags.compatibility)
def short_term_storage_check(app_configs, **kwargs):  # type: ignore[reportMissingParameterType]
    if SHORT_TERM_STORAGE_KEY not in settings.STORAGES:
        if settings.SHORT_TERM_STORAGE_ENABLED:
            return [Error(f"SHORT_TERM_STORAGE_ENABLED is set but STORAGES[{SHORT_TERM_STORAGE_KEY!r}] is not defined")]
        return []

    long_term_target = get_storage_target(settings.STORAGES[DEFAULT_STORAGE_KEY], media_root=settings.MEDIA_ROOT)
    short_term_target = get_storage_target(settings.STORAGES[SHORT_TERM_STORAGE_KEY], media_root=settings.MEDIA_ROOT)
    if long_term_target == short_term_target:
        return [
            Error(
                f"Short-term and long-term storages write to the same place: {short_term_target}",
                hint="Use a different SHORT_TERM_STORAGE_FS_ROOT, bucket or endpoint for the short-term storage",
            ),
        ]
    return []

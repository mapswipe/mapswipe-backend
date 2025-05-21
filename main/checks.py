from pydoc import locate

from django.core.checks import Error, Tags, register


@register(Tags.compatibility)
def celery_beat_tasks(app_configs, **kwargs):
    from main.cronjobs import SCHEDULES

    # Confirm all tasks can be imported
    errors = []
    for name, config in SCHEDULES.items():
        if locate(config.task) is None:
            errors.append(Error(f"Celery beat <{name}> task is incorrect: {config.task}"))

    return errors

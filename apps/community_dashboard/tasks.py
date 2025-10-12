import logging

from celery import shared_task

from apps.community_dashboard.management.commands.update_aggregated_data import Command as UpdateAggregateCommand
from main.cache import CeleryLock
from main.cronjobs import TimeConstants

logger = logging.getLogger(__name__)


@shared_task
def update_aggregated_data():
    with CeleryLock.redis_lock(
        CeleryLock.Key.COMMUNITY_DASHBOARD_UPDATE_AGGREGATE,
        lock_expire=TimeConstants.SECONDS_IN_A_HOUR,
    ) as acquired:
        if not acquired:
            logger.warning("Community Dashboard update aggregate already running")
            return

    UpdateAggregateCommand().handle()

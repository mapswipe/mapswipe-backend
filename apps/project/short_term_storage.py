"""Promote exports of ended projects from the short-term storage to the long-term storage.

- promote: copy short_term_file to file (same name) for FINISHED/WITHDRAWN projects whose exports are unchanged
  for SHORT_TERM_STORAGE_PROMOTION_COOLDOWN_DAYS.
- cleanup: delete short_term_file SHORT_TERM_STORAGE_TTL_DAYS after promotion.

Both periods are shortened by SCHEDULE_GRACE, so the weekly run's start time jitter doesn't delay items by another week.
"""

import dataclasses
import datetime
import logging

from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.common.models import AssetTypeEnum
from apps.project.models import ProjectAsset, ProjectStatusEnum
from main.cache import CeleryLock
from main.logging import log_extra
from main.sentry import SentryTag, capture_grouped_error

logger = logging.getLogger(__name__)

SHORT_TERM_PROMOTION_FAILED_FINGERPRINT = "short-term-promotion-failed"
SHORT_TERM_CLEANUP_FAILED_FINGERPRINT = "short-term-cleanup-failed"

PROMOTABLE_PROJECT_STATUSES = (ProjectStatusEnum.FINISHED, ProjectStatusEnum.WITHDRAWN)

SCHEDULE_GRACE = datetime.timedelta(hours=12)
# Holds PROJECT_EXPORTS_GENERATE while copying or deleting all export files of a project
PROJECT_LOCK_EXPIRE = 60 * 60

# OverwritableFileField stores "" as NULL
_HAS_FILE = Q(file__isnull=False)
_HAS_SHORT_TERM_FILE = Q(short_term_file__isnull=False)


@dataclasses.dataclass
class ShortTermStorageSummary:
    """Counts of projects, except cleaned which counts export assets."""

    promoted: int = 0
    skipped_cooldown: int = 0
    skipped_locked: int = 0
    failed: int = 0
    cleaned: int = 0
    cleanup_skipped_locked: int = 0
    cleanup_failed: int = 0


def _export_assets() -> QuerySet[ProjectAsset]:
    return ProjectAsset.objects.filter(type=AssetTypeEnum.EXPORT)


def _pending_promotion_assets() -> QuerySet[ProjectAsset]:
    return _export_assets().filter(_HAS_SHORT_TERM_FILE).exclude(_HAS_FILE)


def _is_in_cooldown(project_id: int, cooldown_since: datetime.datetime) -> bool:
    return _export_assets().filter(project_id=project_id, modified_at__gte=cooldown_since).exists()


def _copy_to_long_term(project_asset: ProjectAsset):
    """Copy short_term_file into file, using the same name."""
    name = project_asset.short_term_file.name
    assert name is not None
    long_term_storage = project_asset.file.storage
    with project_asset.short_term_file.open("rb") as fp:
        saved_name = long_term_storage.save(name, fp, max_length=project_asset.file.field.max_length)
    if saved_name != name:
        raise Exception(f"Long-term file name {saved_name!r} doesn't match the short-term file name {name!r}")
    project_asset.file = saved_name


def _promote_project(project_id: int, *, now: datetime.datetime, cooldown_since: datetime.datetime) -> bool:
    """Promote the export assets of the project. Return False if the project is in cooldown."""
    with transaction.atomic():
        if _is_in_cooldown(project_id, cooldown_since):
            return False
        project_assets = _pending_promotion_assets().filter(project_id=project_id).select_for_update()
        for project_asset in project_assets:
            _copy_to_long_term(project_asset)
            project_asset.promoted_at = now
            project_asset.save(update_fields=("file", "promoted_at"))
    return True


def promote(summary: ShortTermStorageSummary):
    now = timezone.now()
    cooldown_since = now - datetime.timedelta(days=settings.SHORT_TERM_STORAGE_PROMOTION_COOLDOWN_DAYS) + SCHEDULE_GRACE

    project_ids = set(
        _pending_promotion_assets()
        .filter(project__status__in=PROMOTABLE_PROJECT_STATUSES)
        .order_by()
        .values_list("project_id", flat=True)
        .distinct(),
    )
    cooldown_project_ids = set(
        _export_assets()
        .filter(project_id__in=project_ids, modified_at__gte=cooldown_since)
        .order_by()
        .values_list("project_id", flat=True)
        .distinct(),
    )
    summary.skipped_cooldown += len(cooldown_project_ids)

    for project_id in sorted(project_ids - cooldown_project_ids):
        with CeleryLock.redis_lock(
            CeleryLock.Key.PROJECT_EXPORTS_GENERATE.format(project_id),
            lock_expire=PROJECT_LOCK_EXPIRE,
        ) as acquired:
            if not acquired:
                logger.warning("Project(id: %s) exports generate is running: skipping promotion", project_id)
                summary.skipped_locked += 1
                continue
            try:
                if _promote_project(project_id, now=now, cooldown_since=cooldown_since):
                    summary.promoted += 1
                else:
                    summary.skipped_cooldown += 1
            except SoftTimeLimitExceeded:
                raise
            except Exception as e:
                logger.warning(
                    "Failed to promote exports to the long-term storage",
                    extra=log_extra(dict(project=project_id)),
                    exc_info=True,
                )
                capture_grouped_error(
                    "Failed to promote project exports to the long-term storage",
                    fingerprint=[SHORT_TERM_PROMOTION_FAILED_FINGERPRINT],
                    tags={SentryTag.Tag.PROJECT: project_id},
                    extra=dict(project_id=project_id, error=repr(e)),
                )
                summary.failed += 1


def _expired_short_term_assets(expired_before: datetime.datetime) -> QuerySet[ProjectAsset]:
    return _export_assets().filter(_HAS_SHORT_TERM_FILE, _HAS_FILE, promoted_at__lt=expired_before)


def _cleanup_project(project_id: int, expired_before: datetime.datetime) -> int:
    cleaned = 0
    project_assets = _expired_short_term_assets(expired_before).filter(project_id=project_id)
    for project_asset in project_assets:
        project_asset.short_term_file.delete(save=False)
        project_asset.save(update_fields=("short_term_file",))
        cleaned += 1
    return cleaned


def cleanup(summary: ShortTermStorageSummary):
    expired_before = timezone.now() - datetime.timedelta(days=settings.SHORT_TERM_STORAGE_TTL_DAYS) + SCHEDULE_GRACE

    project_ids = set(_expired_short_term_assets(expired_before).order_by().values_list("project_id", flat=True).distinct())

    for project_id in sorted(project_ids):
        with CeleryLock.redis_lock(
            CeleryLock.Key.PROJECT_EXPORTS_GENERATE.format(project_id),
            lock_expire=PROJECT_LOCK_EXPIRE,
        ) as acquired:
            if not acquired:
                logger.warning("Project(id: %s) exports generate is running: skipping cleanup", project_id)
                summary.cleanup_skipped_locked += 1
                continue
            try:
                summary.cleaned += _cleanup_project(project_id, expired_before)
            except SoftTimeLimitExceeded:
                raise
            except Exception as e:
                logger.warning(
                    "Failed to delete promoted exports from the short-term storage",
                    extra=log_extra(dict(project=project_id)),
                    exc_info=True,
                )
                capture_grouped_error(
                    "Failed to delete promoted project exports from the short-term storage",
                    fingerprint=[SHORT_TERM_CLEANUP_FAILED_FINGERPRINT],
                    tags={SentryTag.Tag.PROJECT: project_id},
                    extra=dict(project_id=project_id, error=repr(e)),
                )
                summary.cleanup_failed += 1


def promote_and_cleanup() -> ShortTermStorageSummary:
    """Promote exports of ended projects and delete expired short-term copies. No-op if short-term storage is disabled."""
    summary = ShortTermStorageSummary()
    if not settings.SHORT_TERM_STORAGE_ENABLED:
        logger.info("Short-term storage is disabled: skipping promotion and cleanup")
        return summary

    promote(summary)
    cleanup(summary)
    logger.info(
        "Short-term storage: promoted=%s skipped_cooldown=%s skipped_locked=%s failed=%s"
        " cleaned=%s cleanup_skipped_locked=%s cleanup_failed=%s",
        summary.promoted,
        summary.skipped_cooldown,
        summary.skipped_locked,
        summary.failed,
        summary.cleaned,
        summary.cleanup_skipped_locked,
        summary.cleanup_failed,
    )
    return summary

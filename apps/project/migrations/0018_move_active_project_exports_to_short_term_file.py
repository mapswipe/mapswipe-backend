# Generated manually

import logging

from django.conf import settings
from django.db import migrations
from django.db.models import F

logger = logging.getLogger(__name__)

# AssetTypeEnum.EXPORT
ASSET_TYPE_EXPORT = 300
# ProjectStatusEnum.PUBLISHED, ProjectStatusEnum.PAUSED
ACTIVE_PROJECT_STATUSES = [50, 60]


def move_exports_to_short_term_file(apps, schema_editor):
    """
    Move the export file name of active projects from `file` (long-term) to `short_term_file`.
    Only the database is changed: the files are copied to the short-term storage outside of Django.
    """
    if not settings.SHORT_TERM_STORAGE_ENABLED:
        logger.info("SHORT_TERM_STORAGE_ENABLED is not set: skipping")
        return

    ProjectAsset = apps.get_model('project', 'ProjectAsset')

    updated_count = ProjectAsset._default_manager.filter(
        type=ASSET_TYPE_EXPORT,
        project__status__in=ACTIVE_PROJECT_STATUSES,
        file__isnull=False,
    ).update(
        short_term_file=F('file'),
        file=None,
        promoted_at=None,
    )
    logger.info(f"Moved {updated_count} export assets to short_term_file")


def move_exports_to_file(apps, schema_editor):
    """
    Move the export file name of active projects from `short_term_file` back to `file`.
    Only the database is changed: the files are not copied back to the long-term storage.
    """
    ProjectAsset = apps.get_model('project', 'ProjectAsset')

    updated_count = ProjectAsset._default_manager.filter(
        type=ASSET_TYPE_EXPORT,
        project__status__in=ACTIVE_PROJECT_STATUSES,
        file__isnull=True,
        short_term_file__isnull=False,
    ).update(
        file=F('short_term_file'),
        short_term_file=None,
    )
    logger.info(f"Moved {updated_count} export assets back to file")


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0017_projectasset_short_term_file'),
    ]

    operations = [
        migrations.RunPython(move_exports_to_short_term_file, move_exports_to_file),
    ]

# Generated manually

import logging

from django.db import migrations

logger = logging.getLogger(__name__)


def migrate_sampling_threshold_to_meters(apps, schema_editor):
    """
    sampling_threshold used to be a float expressed in kilometers
    (StreetMapillaryImageFilters.sampling_threshold: PydanticFloat) and is now a
    strict non-negative integer expressed in meters (StreetMapillaryConfig.sampling_threshold:
    PydanticStrictNonNegativeInt). Convert existing values from km to m so they conform to
    the updated schema and unit. Values that are not positive in meters are
    dropped, which disables sampling.
    """
    Project = apps.get_model('project', 'Project')

    to_update = []
    for project in Project._default_manager.filter(project_type=7):  # STREET type
        if not isinstance(project.project_type_specifics, dict):
            continue

        filters = project.project_type_specifics.get('mapillary')
        if not isinstance(filters, dict):
            continue

        sampling_threshold_km = filters.get('sampling_threshold')
        # NOTE: bool is a subclass of int
        if not isinstance(sampling_threshold_km, (int, float)) or isinstance(sampling_threshold_km, bool):
            continue

        sampling_threshold_m = round(sampling_threshold_km * 1000)
        if sampling_threshold_m <= 0:
            # NOTE: A missing sampling_threshold disables sampling
            logger.info(
                f"Dropping sampling_threshold {sampling_threshold_km} km for project {project.id}"
            )
            del filters['sampling_threshold']
        else:
            logger.info(
                f"Converting sampling_threshold from {sampling_threshold_km} km to "
                f"{sampling_threshold_m} m for project {project.id}"
            )
            filters['sampling_threshold'] = sampling_threshold_m
        to_update.append(project)

    updated_count = Project._default_manager.bulk_update(to_update, ['project_type_specifics'])
    logger.info(f"Field migration completed: {updated_count} projects migrated sampling_threshold from km to m")


def reverse_sampling_threshold_migration(apps, schema_editor):
    """
    Convert sampling_threshold back from meters (int) to kilometers (float).
    """
    Project = apps.get_model('project', 'Project')

    to_update = []
    for project in Project._default_manager.filter(project_type=7):  # STREET type
        if not isinstance(project.project_type_specifics, dict):
            continue

        filters = project.project_type_specifics.get('mapillary')
        if not isinstance(filters, dict):
            continue

        sampling_threshold_m = filters.get('sampling_threshold')
        if not isinstance(sampling_threshold_m, int) or isinstance(sampling_threshold_m, bool):
            continue

        sampling_threshold_km = sampling_threshold_m / 1000
        logger.info(
            f"Reverting sampling_threshold from {sampling_threshold_m} m to "
            f"{sampling_threshold_km} km for project {project.id}"
        )
        filters['sampling_threshold'] = sampling_threshold_km
        to_update.append(project)

    updated_count = Project._default_manager.bulk_update(to_update, ['project_type_specifics'])
    logger.info(f"Reverse migration completed: {updated_count} projects reverted sampling_threshold from m to km")


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0015_merge_20260903_1455'),
    ]

    operations = [
        migrations.RunPython(migrate_sampling_threshold_to_meters, reverse_sampling_threshold_migration),
    ]

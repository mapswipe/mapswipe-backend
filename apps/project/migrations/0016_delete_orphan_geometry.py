from django.db import migrations

BATCH_SIZE = 500


def delete_orphan_geometry(apps, schema_editor):
    """Delete geometry rows that no project references."""
    Geometry = apps.get_model("project", "Geometry")
    Project = apps.get_model("project", "Project")

    referenced_geometry_ids = Project._default_manager.filter(
        aoi_geometry__isnull=False,
    ).values("aoi_geometry_id")

    orphan_ids = list(
        Geometry._default_manager.exclude(pk__in=referenced_geometry_ids).values_list("pk", flat=True),
    )

    for start in range(0, len(orphan_ids), BATCH_SIZE):
        Geometry._default_manager.filter(pk__in=orphan_ids[start : start + BATCH_SIZE]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("project", "0015_alter_project_aoi_geometry"),
    ]

    operations = [
        migrations.RunPython(
            delete_orphan_geometry,
            reverse_code=migrations.RunPython.noop,
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0014_remove_project_unique_project_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='firebase_push_requested_version',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='project',
            name='firebase_pushed_version',
            field=models.PositiveIntegerField(default=0),
        ),
    ]

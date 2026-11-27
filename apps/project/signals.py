import typing

from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Geometry, Project


@receiver(post_delete, sender=Project, dispatch_uid="project_delete_orphan_aoi_geometry")
def delete_orphan_aoi_geometry(
    sender: type[Project],
    instance: Project,
    using: str,
    **kwargs: typing.Any,
) -> None:
    """Delete the geometry owned by a deleted project.

    Project holds the relation, so the geometry row is not collected along with the project.
    """
    if instance.aoi_geometry_id is None:
        return

    Geometry.objects.using(using).filter(pk=instance.aoi_geometry_id).delete()

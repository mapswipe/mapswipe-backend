import strawberry

from project_types.tile_map_service.find import project as find_project

# NOTE: We are importing base just for side-effect
from . import base  # type: ignore[reportUnusedImport]  # noqa: F401


@strawberry.experimental.pydantic.type(model=find_project.FindProjectProperty, all_fields=True)
class FindProjectPropertyType: ...

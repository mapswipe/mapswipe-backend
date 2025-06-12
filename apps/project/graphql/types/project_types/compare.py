import strawberry

from project_types.tile_map_service.compare import project as compare_project

# NOTE: We are importing base just for side-effect
from . import base  # type: ignore[reportUnusedImport]  # noqa: F401


@strawberry.experimental.pydantic.type(model=compare_project.CompareProjectProperty, all_fields=True)
class CompareProjectPropertyType: ...

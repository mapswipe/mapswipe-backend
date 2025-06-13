import strawberry

from project_types.tile_map_service.compare import project as compare_project


@strawberry.experimental.pydantic.type(model=compare_project.CompareProjectProperty, all_fields=True)
class CompareProjectPropertyType: ...

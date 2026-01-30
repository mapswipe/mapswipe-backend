import strawberry

from project_types.tile_map_service.locate import project as locate_project


@strawberry.experimental.pydantic.type(model=locate_project.LocateProjectProperty, all_fields=True)
class LocateProjectPropertyType: ...

import strawberry

from project_types.tile_map_service.find import project as find_project


@strawberry.experimental.pydantic.type(model=find_project.FindProjectProperty, all_fields=True)
class FindProjectPropertyType: ...

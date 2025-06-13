import strawberry

from project_types.tile_map_service.find import project as find_project


@strawberry.experimental.pydantic.input(model=find_project.FindProjectProperty, all_fields=True)
class FindProjectPropertyInput: ...

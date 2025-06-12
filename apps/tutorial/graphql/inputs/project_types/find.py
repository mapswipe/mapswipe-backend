import strawberry

from project_types.tile_map_service.find import tutorial as find_tutorial


@strawberry.experimental.pydantic.input(model=find_tutorial.FindTutorialTaskProperty, all_fields=True)
class FindTutorialTaskPropertyInput: ...

import strawberry

from project_types.tile_map_service.compare import tutorial as compare_tutorial


@strawberry.experimental.pydantic.input(model=compare_tutorial.CompareTutorialTaskProperty, all_fields=True)
class CompareTutorialTaskPropertyInput: ...

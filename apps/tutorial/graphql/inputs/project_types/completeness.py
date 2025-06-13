import strawberry

from project_types.tile_map_service.completeness import tutorial as completeness_tutorial


@strawberry.experimental.pydantic.input(model=completeness_tutorial.CompletenessTutorialTaskProperty, all_fields=True)
class CompletenessTutorialTaskPropertyInput: ...

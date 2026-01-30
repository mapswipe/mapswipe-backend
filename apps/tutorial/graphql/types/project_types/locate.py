import strawberry

from project_types.tile_map_service.locate import tutorial as locate_tutorial


@strawberry.experimental.pydantic.type(model=locate_tutorial.LocateTutorialTaskProperty, all_fields=True)
class LocateTutorialTaskPropertyType: ...

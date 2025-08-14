import strawberry

from project_types.street import tutorial as street_tutorial


@strawberry.experimental.pydantic.type(model=street_tutorial.StreetTutorialTaskProperty, all_fields=True)
class StreetTutorialTaskPropertyType: ...

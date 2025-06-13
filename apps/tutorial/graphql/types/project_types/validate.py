import strawberry

from project_types.validate import tutorial as validate_tutorial


@strawberry.experimental.pydantic.type(model=validate_tutorial.ValidateTutorialTaskProperty, all_fields=True)
class ValidateTutorialTaskPropertyType: ...

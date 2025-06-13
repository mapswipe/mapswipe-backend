import strawberry

from project_types.validate import tutorial as validate_tutorial


@strawberry.experimental.pydantic.input(model=validate_tutorial.ValidateTutorialTaskProperty, all_fields=True)
class ValidateTutorialTaskPropertyInput: ...

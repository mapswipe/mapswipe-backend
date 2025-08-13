import strawberry

from project_types.street import project as street_project


@strawberry.experimental.pydantic.input(model=street_project.ValidateObjectSourceConfig, all_fields=True)
class ValidateObjectSourceConfigInput: ...


@strawberry.experimental.pydantic.input(model=street_project.ValidateProjectProperty, all_fields=True)
class ValidateProjectPropertyInput: ...

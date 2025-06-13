import strawberry

from project_types.validate import project as validate_project


@strawberry.experimental.pydantic.type(model=validate_project.ValidateObjectSourceConfig, all_fields=True)
class ValidateObjectSourceConfig: ...


@strawberry.experimental.pydantic.type(model=validate_project.ValidateProjectProperty, all_fields=True)
class ValidateProjectPropertyType: ...

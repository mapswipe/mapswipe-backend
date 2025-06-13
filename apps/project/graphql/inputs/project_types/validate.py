import strawberry

from project_types.validate import project as validate_project


@strawberry.experimental.pydantic.input(model=validate_project.ValidateObjectSourceConfig, all_fields=True)
class ValidateObjectSourceConfigInput: ...


# FIXME(tnagorra): Add one_of here?
@strawberry.experimental.pydantic.input(model=validate_project.ValidateProjectProperty, all_fields=True)
class ValidateProjectPropertyInput: ...

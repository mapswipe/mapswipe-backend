import strawberry

from project_types.conflation import project as conflation_project


@strawberry.experimental.pydantic.input(model=conflation_project.ConflationObjectSourceConfig, all_fields=True)
class ConflationObjectSourceConfigInput: ...


@strawberry.experimental.pydantic.input(model=conflation_project.ConflationProjectProperty, all_fields=True)
class ConflationProjectPropertyInput: ...

import strawberry

from project_types.conflation import project as conflation_project


@strawberry.experimental.pydantic.type(model=conflation_project.ConflationObjectSourceConfig, all_fields=True)
class ConflationObjectSourceConfig: ...


@strawberry.experimental.pydantic.type(model=conflation_project.ConflationProjectProperty, all_fields=True)
class ConflationProjectPropertyType: ...


DEFAULT_TEST_RESPONSE_ERROR_MESSAGE: str = "Something unexpected has occurred. Please contact an admin to fix this issue."

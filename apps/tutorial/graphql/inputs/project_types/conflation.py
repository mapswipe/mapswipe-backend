import strawberry

from project_types.conflation import tutorial as conflation_tutorial


@strawberry.experimental.pydantic.input(model=conflation_tutorial.ConflationTutorialTaskProperty, all_fields=True)
class ConflationTutorialTaskPropertyInput: ...

import strawberry

from project_types.conflation import tutorial as conflation_tutorial


@strawberry.experimental.pydantic.type(model=conflation_tutorial.ConflationTutorialTaskProperty, all_fields=True)
class ConflationTutorialTaskPropertyType: ...

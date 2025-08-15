import strawberry

from project_types.street import project as street_project


@strawberry.experimental.pydantic.input(model=street_project.StreetMappilaryImageFilters, all_fields=True)
class StreetMappilaryImageFiltersInput: ...


@strawberry.experimental.pydantic.input(model=street_project.StreetProjectProperty, all_fields=True)
class StreetProjectPropertyInput: ...

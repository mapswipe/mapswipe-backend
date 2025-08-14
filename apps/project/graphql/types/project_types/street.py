import strawberry

from project_types.street import project as street_project


@strawberry.experimental.pydantic.type(model=street_project.StreetMappilaryImageFilters, all_fields=True)
class StreetMappilaryImageFilters: ...


@strawberry.experimental.pydantic.type(model=street_project.StreetProjectProperty, all_fields=True)
class StreetProjectPropertyType: ...

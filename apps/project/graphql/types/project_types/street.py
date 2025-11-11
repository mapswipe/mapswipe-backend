import strawberry

from project_types.street import project as street_project


@strawberry.experimental.pydantic.type(model=street_project.StreetMapillaryImageFilters, all_fields=True)
class StreetMapillaryImageFilters: ...


@strawberry.experimental.pydantic.type(model=street_project.StreetImageProvider, all_fields=True)
class StreetImageProvider: ...


@strawberry.experimental.pydantic.type(model=street_project.StreetProjectProperty, all_fields=True)
class StreetProjectPropertyType: ...

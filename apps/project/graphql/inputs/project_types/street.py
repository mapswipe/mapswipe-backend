import strawberry

from project_types.street import project as street_project
from utils.geo.street_image_provider.models import StreetImageProvider


@strawberry.experimental.pydantic.input(model=street_project.StreetImageFilters, all_fields=True)
class StreetImageFiltersInput: ...


@strawberry.experimental.pydantic.input(model=StreetImageProvider, all_fields=True)
class StreetImageProviderInput: ...


@strawberry.experimental.pydantic.input(model=street_project.StreetProjectProperty, all_fields=True)
class StreetProjectPropertyInput: ...

import strawberry

from project_types.street import project as street_project
from utils.geo.street_image_provider.models import StreetImageProvider as StreetImageProviderModel


@strawberry.experimental.pydantic.type(model=street_project.StreetMapillaryImageFilters, all_fields=True)
class StreetMapillaryImageFilters: ...


@strawberry.experimental.pydantic.type(model=StreetImageProviderModel, all_fields=True)
class StreetImageProvider: ...


@strawberry.experimental.pydantic.type(model=street_project.StreetProjectProperty, all_fields=True)
class StreetProjectPropertyType: ...

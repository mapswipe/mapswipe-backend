import strawberry

from project_types.street import project as street_project
from utils.geo.street_image_provider import models as street_image_provider_models


@strawberry.experimental.pydantic.type(model=street_image_provider_models.StreetMapillaryConfig, all_fields=True)
class StreetMapillaryConfig: ...


@strawberry.experimental.pydantic.type(model=street_image_provider_models.StreetPanoramaxConfig, all_fields=True)
class StreetPanoramaxConfig: ...


@strawberry.experimental.pydantic.type(model=street_image_provider_models.StreetPanoramaxCustomConfig, all_fields=True)
class StreetPanoramaxCustomConfig: ...


@strawberry.experimental.pydantic.type(model=street_project.StreetProjectProperty, all_fields=True)
class StreetProjectPropertyType: ...

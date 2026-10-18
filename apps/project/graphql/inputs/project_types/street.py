import strawberry

from project_types.street import project as street_project
from utils.geo.street_image_provider import models as street_image_provider_models


@strawberry.experimental.pydantic.input(model=street_image_provider_models.StreetMapillaryConfig, all_fields=True)
class StreetMapillaryConfigInput: ...


@strawberry.experimental.pydantic.input(model=street_image_provider_models.StreetPanoramaxConfig, all_fields=True)
class StreetPanoramaxConfigInput: ...


@strawberry.experimental.pydantic.input(model=street_image_provider_models.StreetPanoramaxCustomConfig, all_fields=True)
class StreetPanoramaxCustomConfigInput: ...


@strawberry.experimental.pydantic.input(model=street_project.StreetProjectProperty, all_fields=True)
class StreetProjectPropertyInput: ...

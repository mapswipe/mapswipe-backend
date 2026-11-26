import typing

import strawberry

from project_types.validate import project as validate_project
from utils import fields

# NOTE: We are importing base for side-effect
# ValidateProjectPropertyType needs the tile server types
from . import base  # noqa: F401  # isort: skip # type: ignore[reportUnusedImport]

if typing.TYPE_CHECKING:
    from apps.project.graphql.types.types import ProjectAssetType


@strawberry.experimental.pydantic.type(model=validate_project.ValidateObjectSourceConfig, all_fields=True)
class ValidateObjectSourceConfig: ...


@strawberry.experimental.pydantic.type(model=validate_project.ValidateProjectProperty, all_fields=True)
class ValidateProjectPropertyType: ...


DEFAULT_TEST_RESPONSE_ERROR_MESSAGE: str = "Something unexpected has occurred. Please contact an admin to fix this issue."


@strawberry.type
class ValidateTestAoiResponse:
    ok: bool = True
    error: str | None = None
    object_count: int | None = None

    # TODO(tnagorra): This needs to be generic. Create a base response class.
    def generate_error(self, message: str = DEFAULT_TEST_RESPONSE_ERROR_MESSAGE):
        self.ok = False
        self.error = message
        return self


@strawberry.type
class ValidateTestObjectSourceResponse(ValidateTestAoiResponse):
    """Response of an object source test that stores the AOI as a temporary project asset."""

    project_id: strawberry.ID | None = None
    aoi_geometry_asset: typing.Annotated["ProjectAssetType", strawberry.lazy("apps.project.graphql.types.types")] | None = (
        None
    )


@strawberry.type
class TestValidateAoiObjectsResponse(ValidateTestAoiResponse):
    project_id: strawberry.ID | None = None
    asset_id: strawberry.ID | None = None
    ohsome_filter: str | None = None


@strawberry.type
class TestValidateTaskingManagerProjectResponse(ValidateTestObjectSourceResponse):
    hot_tm_id: fields.PydanticId | None = None
    ohsome_filter: str | None = None


@strawberry.type
class TestValidateObjectGeojsonUrlResponse(ValidateTestObjectSourceResponse):
    object_geojson_url: str | None = None

import strawberry

from project_types.validate import project as validate_project
from utils import fields


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
    ohsome_filter: str | None = None

    def generate_error(self, message: str = DEFAULT_TEST_RESPONSE_ERROR_MESSAGE):
        self.ok = False
        self.error = message
        return self


@strawberry.type
class TestValidateAoiObjectsResponse(ValidateTestAoiResponse):
    project_id: strawberry.ID | None = None
    asset_id: strawberry.ID | None = None


@strawberry.type
class TestValidateTaskingManagerProjectResponse(ValidateTestAoiResponse):
    hot_tm_id: fields.PydanticId | None = None

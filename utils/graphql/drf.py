import typing

import strawberry
from pydantic import ValidationError as PydanticValidationError
from rest_framework import serializers

from utils.common import to_camel_case, to_snake_case

from .types import CustomErrorType

ARRAY_NON_MEMBER_ERRORS = "nonMemberErrors"


@strawberry.type
class ArrayNestedErrorType:
    client_id: str
    messages: str | None
    object_errors: list[CustomErrorType | None] | None

    def keys(self):
        return ["client_id", "messages", "object_errors"]

    def __getitem__(self, key: str):
        key = to_snake_case(key)
        if key in ("object_errors",) and getattr(self, key):
            return [dict(each) for each in getattr(self, key)]
        return getattr(self, key)


@strawberry.type
class MutationCustomErrorType:
    field: str
    client_id: str | None = None
    messages: str | None
    object_errors: list[CustomErrorType | None] | None
    array_errors: list[ArrayNestedErrorType | None] | None
    pydantic_errors: list[CustomErrorType] | None = None

    DEFAULT_ERROR_MESSAGE: str = "Something unexpected has occurred. Please contact an admin to fix this issue."

    @staticmethod
    def generate_message(message: str = DEFAULT_ERROR_MESSAGE) -> CustomErrorType:
        return CustomErrorType(
            [
                dict(
                    field="nonFieldErrors",
                    messages=message,
                    object_errors=None,
                    array_errors=None,
                ),
            ],
        )

    def keys(self):
        return ["field", "client_id", "messages", "object_errors", "array_errors", "pydantic_errors"]

    def __getitem__(self, key: str):
        key = to_snake_case(key)
        if key in ("object_errors", "array_errors") and getattr(self, key):
            # TODO(thenav56): Confirm if using str() is enough
            if key == "object_errors":
                return {each_key: str(each_data) for each_key, each_data in getattr(self, key).items()}
            return [str(each) for each in getattr(self, key)]
        return getattr(self, key)


# TODO(thenav56): Check again on the error structure
def handle_pydantic_validation_error(
    key: str,
    pydantic_error: PydanticValidationError,
) -> serializers.ValidationError:
    return serializers.ValidationError(
        {
            f"{key}-pydantic": pydantic_error.errors(
                include_context=False,
                include_url=False,
            ),
        },  # type: ignore[reportArgumentType]
    )


def _serializer_error_to_error_types(
    errors: dict[str, list[CustomErrorType] | None],
    initial_data: dict[typing.Any, typing.Any] | None = None,
) -> list[typing.Any]:
    initial_data = initial_data or {}
    node_client_id = initial_data.get("client_id")
    error_types: list[MutationCustomErrorType] = []
    for field, value in errors.items():
        if field.endswith("-pydantic"):
            error_types.append(
                MutationCustomErrorType(
                    client_id=node_client_id,
                    field=to_camel_case(field.replace("-pydantic", "")),
                    object_errors=None,
                    array_errors=None,
                    messages=None,
                    # NOTE: Error from handle_pydantic_validation_error
                    pydantic_errors=value,
                ),
            )
            continue
        if isinstance(value, dict):
            error_types.append(
                MutationCustomErrorType(
                    client_id=node_client_id,
                    field=to_camel_case(field),
                    object_errors=value,  # type: ignore[reportArgumentType]
                    array_errors=None,
                    messages=None,
                ),
            )
        elif isinstance(value, list):
            if isinstance(value[0], str):  # type: ignore[reportUnnecessaryIsInstance]
                if isinstance(initial_data.get(field), list):
                    # we have found an array input with top level error
                    error_types.append(
                        MutationCustomErrorType(
                            client_id=node_client_id,
                            field=to_camel_case(field),
                            array_errors=[
                                ArrayNestedErrorType(
                                    client_id=ARRAY_NON_MEMBER_ERRORS,
                                    messages="".join(str(msg) for msg in value),
                                    object_errors=None,
                                ),
                            ],
                            messages=None,
                            object_errors=None,
                        ),
                    )
                else:
                    error_types.append(
                        MutationCustomErrorType(
                            client_id=node_client_id,
                            field=to_camel_case(field),
                            messages=", ".join(str(msg) for msg in value),
                            object_errors=None,
                            array_errors=None,
                        ),
                    )
            elif isinstance(value[0], dict):  # type: ignore[reportUnnecessaryIsInstance]
                array_errors = []
                for pos, array_item in enumerate(value):
                    if not array_item:
                        # array item might not have error
                        continue
                    # fetch array.item.client_id from the initial data
                    array_client_id = initial_data[field][pos].get("client_id", f"NOT_FOUND_{pos}")
                    array_errors.append(
                        ArrayNestedErrorType(
                            client_id=array_client_id,
                            object_errors=_serializer_error_to_error_types(array_item, initial_data[field][pos]),  # type: ignore[reportArgumentType]
                            messages=None,
                        ),
                    )
                error_types.append(
                    MutationCustomErrorType(
                        client_id=node_client_id,
                        field=to_camel_case(field),
                        array_errors=array_errors,
                        object_errors=None,
                        messages=None,
                    ),
                )
        else:
            # fallback
            error_types.append(
                MutationCustomErrorType(
                    field=to_camel_case(field),
                    messages=" ".join(str(msg) for msg in value or []),
                    array_errors=None,
                    object_errors=None,
                ),
            )
    return error_types


def mutation_is_not_valid(serializer: typing.Any) -> CustomErrorType | None:
    """Checks if serializer is valid, if not returns list of errorTypes."""
    if not serializer.is_valid():
        errors = _serializer_error_to_error_types(serializer.errors, serializer.initial_data)
        return CustomErrorType([dict(each) for each in errors])
    return None

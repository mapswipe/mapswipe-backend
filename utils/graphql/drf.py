import typing

import strawberry
from pydantic import ValidationError as PydanticValidationError
from rest_framework import serializers

from utils.common import to_camel_case, to_snake_case

from .types import CustomErrorType

ARRAY_NON_MEMBER_ERRORS = "nonMemberErrors"


# NOTE: Recursively iterate over dict and list and convert strawberry type object to dict
def recursive_dict(data: typing.Any):
    if isinstance(data, dict):
        new_obj = {}
        for key, value in data.items():
            new_obj[key] = recursive_dict(value)
        return new_obj
    if isinstance(data, list):
        return [recursive_dict(item) for item in data]
    if isinstance(data, ArrayNestedErrorType):
        return dict(data)
    if isinstance(data, MutationCustomErrorType):
        return dict(data)
    return data


@strawberry.type
class ArrayNestedErrorType:
    client_id: str
    messages: str | None
    object_errors: list[CustomErrorType | None] | None

    def keys(self):
        return ["client_id", "messages", "object_errors"]

    def __getitem__(self, key: str):
        key = to_snake_case(key)
        attr_value = getattr(self, key)
        if key == "object_errors" and attr_value:
            return [recursive_dict(each) for each in attr_value]
        return attr_value


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
        attr_value = getattr(self, key)
        if key == "object_errs" and attr_value:
            return {each_key: recursive_dict(each_data) for each_key, each_data in attr_value.items()}
        if key == "array_errors" and attr_value:
            return [recursive_dict(each) for each in attr_value]
        return attr_value


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
            err = MutationCustomErrorType(
                client_id=node_client_id,
                field=to_camel_case(field.replace("-pydantic", "")),
                object_errors=None,
                array_errors=None,
                messages=None,
                # NOTE: Error from handle_pydantic_validation_error
                pydantic_errors=value,
            )
            error_types.append(err)
            continue
        if isinstance(value, dict):
            err = MutationCustomErrorType(
                client_id=node_client_id,
                field=to_camel_case(field),
                object_errors=value,  # type: ignore[reportArgumentType]
                array_errors=None,
                messages=None,
            )
            error_types.append(err)
        elif isinstance(value, list):
            if isinstance(value[0], str):  # type: ignore[reportUnnecessaryIsInstance]
                if isinstance(initial_data.get(field), list):
                    # we have found an array input with top level error
                    err = MutationCustomErrorType(
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
                    )
                else:
                    err = MutationCustomErrorType(
                        client_id=node_client_id,
                        field=to_camel_case(field),
                        messages=", ".join(str(msg) for msg in value),
                        object_errors=None,
                        array_errors=None,
                    )
                    error_types.append(err)
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
                err = MutationCustomErrorType(
                    client_id=node_client_id,
                    field=to_camel_case(field),
                    array_errors=array_errors,
                    object_errors=None,
                    messages=None,
                )
                error_types.append(err)
        else:
            # fallback
            err = MutationCustomErrorType(
                field=to_camel_case(field),
                messages=" ".join(str(msg) for msg in value or []),
                array_errors=None,
                object_errors=None,
            )
            error_types.append(err)
    return error_types


def mutation_is_not_valid(serializer: typing.Any) -> CustomErrorType | None:
    """Checks if serializer is valid, if not returns list of errorTypes."""
    if not serializer.is_valid():
        errors = _serializer_error_to_error_types(serializer.errors, serializer.initial_data)
        return CustomErrorType([dict(each) for each in errors])
    return None

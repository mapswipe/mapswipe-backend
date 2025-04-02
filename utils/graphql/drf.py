import re

import strawberry
from pydantic import ValidationError as PydanticValidationError
from rest_framework import serializers

from .types import CustomErrorType


# Adapted from this response in Stackoverflow
# http://stackoverflow.com/a/19053800/1072990
def to_camel_case(snake_str):
    components = snake_str.split("_")
    # We capitalize the first letter of each component except the first one
    # with the 'capitalize' method and join them together.
    return components[0] + "".join(x.capitalize() if x else "_" for x in components[1:])


def to_snake_case(name):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


ARRAY_NON_MEMBER_ERRORS = "nonMemberErrors"


@strawberry.type
class ArrayNestedErrorType:
    client_id: str
    messages: str | None
    object_errors: list[CustomErrorType | None] | None

    def keys(self):
        return ["client_id", "messages", "object_errors"]

    def __getitem__(self, key):
        key = to_snake_case(key)
        if key in ("object_errors",) and getattr(self, key):
            return [dict(each) for each in getattr(self, key)]
        return getattr(self, key)


@strawberry.type
class _CustomErrorType:
    field: str
    client_id: str | None = None
    messages: str | None
    object_errors: list[CustomErrorType | None] | None
    array_errors: list[ArrayNestedErrorType | None] | None
    pydantic_errors: list[CustomErrorType] | None = None

    DEFAULT_ERROR_MESSAGE = "Something unexpected has occurred. Please contact an admin to fix this issue."

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

    def __getitem__(self, key):
        key = to_snake_case(key)
        if key in ("object_errors", "array_errors") and getattr(self, key):
            return [dict(each) for each in getattr(self, key)]
        return getattr(self, key)


# TODO: Check again on the error structure
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
        },
    )


def serializer_error_to_error_types(errors: dict, initial_data: dict | None = None) -> list:
    initial_data = initial_data or {}
    node_client_id = initial_data.get("client_id")
    error_types = []
    for field, value in errors.items():
        if field.endswith("-pydantic"):
            error_types.append(
                _CustomErrorType(
                    client_id=node_client_id,
                    field=to_camel_case(field.replace("-pydantic", "")),
                    object_errors=None,
                    array_errors=None,
                    messages=None,
                    # NOTE: Error from handle_pydantic_validation_error
                    pydantic_errors=value,  # type: ignore[reportGeneralTypeIssues]
                ),
            )
            continue
        if isinstance(value, dict):
            error_types.append(
                _CustomErrorType(
                    client_id=node_client_id,
                    field=to_camel_case(field),
                    object_errors=value,  # type: ignore[reportGeneralTypeIssues]
                    array_errors=None,
                    messages=None,
                ),
            )
        elif isinstance(value, list):
            if isinstance(value[0], str):
                if isinstance(initial_data.get(field), list):
                    # we have found an array input with top level error
                    error_types.append(
                        _CustomErrorType(
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
                        _CustomErrorType(
                            client_id=node_client_id,
                            field=to_camel_case(field),
                            messages=", ".join(str(msg) for msg in value),
                            object_errors=None,
                            array_errors=None,
                        ),
                    )
            elif isinstance(value[0], dict):
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
                            object_errors=serializer_error_to_error_types(array_item, initial_data[field][pos]),
                            messages=None,
                        ),
                    )
                error_types.append(
                    _CustomErrorType(
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
                _CustomErrorType(
                    field=to_camel_case(field),
                    messages=" ".join(str(msg) for msg in value),
                    array_errors=None,
                    object_errors=None,
                ),
            )
    return error_types


def mutation_is_not_valid(serializer) -> CustomErrorType | None:
    """
    Checks if serializer is valid, if not returns list of errorTypes
    """
    if not serializer.is_valid():
        errors = serializer_error_to_error_types(serializer.errors, serializer.initial_data)
        return CustomErrorType([dict(each) for each in errors])
    return None

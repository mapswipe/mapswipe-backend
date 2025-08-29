import typing
from dataclasses import Field, is_dataclass

import strawberry


class DataclassInstance(typing.Protocol):
    __dataclass_fields__: typing.ClassVar[dict[str, Field[typing.Any]]]


InputDataType = DataclassInstance | tuple[typing.Any] | list[typing.Any] | typing.Any


def parse_input_data(
    data: InputDataType,
    dataclass_transformer: typing.Callable[[DataclassInstance], tuple[bool, InputDataType]] | None = None,
):
    """Return dict from Strawberry Input Object.

    NOTE: strawberry.asdict doesn't handle nested and strawberry.UNSET
    Related issue: https://github.com/strawberry-graphql/strawberry/issues/3265
    https://github.com/strawberry-graphql/strawberry/blob/d2c0fb4d2d363929c9ac10161884d004ab9cf555/strawberry/object_type.py#L395
    """
    # TODO(thenav56): Write test
    if type(data) is tuple:
        # NOTE: We need to filter out the response as we can return None when deleting items
        return [item for item in (parse_input_data(datum, dataclass_transformer) for datum in data) if item is not None]

    if type(data) is list:
        # NOTE: We need to filter out the response as we can return None when deleting items
        return [item for item in (parse_input_data(datum, dataclass_transformer) for datum in data) if item is not None]

    if not is_dataclass(data) or isinstance(data, type):
        return data

    if dataclass_transformer:
        handled, update = dataclass_transformer(data)
        if handled:
            return parse_input_data(update, dataclass_transformer)

    native_dict = {}
    for key, value in data.__dict__.items():
        if value == strawberry.UNSET:
            continue
        native_dict[key] = parse_input_data(value, dataclass_transformer)
    return native_dict

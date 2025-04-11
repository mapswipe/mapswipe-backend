from dataclasses import is_dataclass

import strawberry


def parse_input_data(data) -> dict | list:
    """
    Return dict from Strawberry Input Object
    NOTE: strawberry.asdict doesn't handle nested and strawberry.UNSET
    Related issue: https://github.com/strawberry-graphql/strawberry/issues/3265
    https://github.com/strawberry-graphql/strawberry/blob/d2c0fb4d2d363929c9ac10161884d004ab9cf555/strawberry/object_type.py#L395

    """
    # TODO: Write test
    if type(data) in [tuple, list]:
        return [parse_input_data(datum) for datum in data]
    native_dict = {}
    for key, value in data.__dict__.items():
        if value == strawberry.UNSET:
            continue
        if isinstance(value, list):
            _list_value = []
            for _value in value:
                if is_dataclass(_value):
                    _list_value.append(parse_input_data(_value))
                else:
                    _list_value.append(_value)
            native_dict[key] = _list_value
            continue
        if is_dataclass(value):
            native_dict[key] = parse_input_data(value)
        else:
            native_dict[key] = value
    return native_dict

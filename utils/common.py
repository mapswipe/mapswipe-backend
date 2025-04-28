import copy
import re
import typing


# TODO(tnagorra): We might also need to support iterating in lists
def clean_up_none_keys(data: dict[typing.Any, typing.Any]):
    """
    Remove keys with none values (Also supports nested dict)
    Input:
     {"a": None, "b": "Hi"}
    Output:
     {"b": "Hi"}
    """
    _clone_data = copy.deepcopy(data)
    for key, value in data.items():
        if value is None:
            _clone_data.pop(key)
        if isinstance(value, dict):
            _clone_data[key] = clean_up_none_keys(value)
    return _clone_data


# Adapted from this response in Stackoverflow
# http://stackoverflow.com/a/19053800/1072990
def to_camel_case(snake_str: str):
    components = snake_str.split("_")
    # We capitalize the first letter of each component except the first one
    # with the 'capitalize' method and join them together.
    return components[0] + "".join(x.capitalize() if x else "_" for x in components[1:])


def to_snake_case(name: str):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def format_object_keys(
    obj: dict[typing.Any, typing.Any] | list[typing.Any] | typing.Any,
    formatter: typing.Callable[[str], str],
):
    if isinstance(obj, dict):
        new_obj = {}
        for key, value in obj.items():
            new_key = formatter(key) if isinstance(key, str) else key
            new_obj[new_key] = format_object_keys(value, formatter)
        return new_obj
    if isinstance(obj, list):
        return [format_object_keys(item, formatter) for item in obj]
    return obj

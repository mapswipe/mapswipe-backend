import copy
import typing


# TODO: We might also need to support iterating in lists
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

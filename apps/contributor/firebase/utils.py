import logging
import typing

from firebase_admin.db import Reference
from pydantic import BaseModel, ValidationError

from main.config import Config

logger = logging.getLogger(__name__)


def get_list_of_items_from_firebase[T: BaseModel](
    model: type[T],
    items_key: str,
    get_item_key: typing.Callable[[str], str],
) -> tuple[list[tuple[str, T]], int, Reference]:
    items_ref = Config.FIREBASE_HELPER.ref(items_key)

    keys = typing.cast("dict[str, bool] | None", items_ref.get())

    # Check if there are any updates
    if not keys:
        logger.info("Found no items on firebase for %s", items_key)
        return ([], 0, items_ref)

    all_keys = keys.keys()
    errored_count = 0

    items_to_pull: list[tuple[str, T]] = []
    for key in all_keys:
        item_ref = Config.FIREBASE_HELPER.ref(get_item_key(key))
        try:
            item = typing.cast("dict[str, typing.Any] | None", item_ref.get())
            if not item:
                raise LookupError(f"Item with key {key} not found")
            item_obj = model.model_validate(item)
        except ValidationError:
            errored_count += 1
            logger.warning("Validation failed for item from firebase: %s", key)
            continue
        except LookupError:
            errored_count += 1
            logger.warning("Item not found in firebase: %s", key)
            continue

        items_to_pull.append((key, item_obj))

    return (items_to_pull, errored_count, items_ref)

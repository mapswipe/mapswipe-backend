import logging
import typing

from firebase_admin.db import Reference
from pydantic import BaseModel, ConfigDict, ValidationError

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
        logger.info("%s items not found on firebase at %s", model.__name__, items_key)
        return ([], 0, items_ref)

    all_keys = keys.keys()
    errored_count = 0

    items_to_pull: list[tuple[str, T]] = []
    for key in all_keys:
        item_ref = Config.FIREBASE_HELPER.ref(get_item_key(key))
        try:
            item = typing.cast("dict[str, typing.Any] | None", item_ref.get())
            if not item:
                raise LookupError(f"{model.__name__} item with key {key} not found")

            class RelaxedModel(model):
                model_config = ConfigDict(extra="ignore")

            # NOTE: we want to ignore extra fields from firebase
            item_obj = RelaxedModel.model_validate(item)
            item_obj = model.model_validate(item_obj)
        except ValidationError:
            errored_count += 1
            # FIXME: Do we need to show actual error?
            logger.warning("Validation failed for %s item from firebase: %s", model.__name__, key)
            continue
        except LookupError:
            errored_count += 1
            logger.warning("%s item not found in firebase: %s", model.__name__, key)
            continue

        items_to_pull.append((key, item_obj))

    return (items_to_pull, errored_count, items_ref)

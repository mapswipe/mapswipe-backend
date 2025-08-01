import logging
import typing
from collections.abc import Callable

from celery import shared_task
from django.core import management
from firebase_admin.db import Reference

from apps.common.models import FirebasePushResource, FirebasePushStatusEnum
from main.cache import CeleryLock
from main.config import Config
from main.logging import log_extra

logger = logging.getLogger(__name__)


class InvalidObjectPushException(Exception): ...


@shared_task
def clear_expired_django_sessions():
    with CeleryLock.redis_lock(CeleryLock.Key.CLEAR_EXPIRED_DJANGO_SESSIONS) as acquired:
        if not acquired:
            logger.warning("Clear expired django sessions")
            return
    management.call_command("clearsessions", verbosity=0)


# TODO(tnagorra): We might need to create a common class
@shared_task
def push_django_to_firebase[T: FirebasePushResource](
    obj_id: int,
    model: type[T],
    handle_new_object_on_firebase: Callable[[T, Reference], None],
    handle_object_update_on_firebase: Callable[[T, Reference], None],
    get_firebase_path: Callable[[str, T], str],
):
    model_obj = model.objects.filter(id=obj_id).first()
    if not model_obj:
        return

    model_obj.update_firebase_push_status(FirebasePushStatusEnum.PROCESSING)

    try:
        model_ref = Config.FIREBASE_HELPER.ref(
            get_firebase_path(model_obj.firebase_id, model_obj),
        )
        fb_model: typing.Any = model_ref.get()

        if not model_obj.firebase_last_pushed:
            if fb_model is not None:
                logger.error(
                    "push_to_firebase found an existing %s in Firebase during creation",
                    model_obj._meta.label,
                    extra=log_extra({"model_obj_id": model_obj.pk}),
                )
                raise InvalidObjectPushException
            handle_new_object_on_firebase(model_obj, model_ref)

        else:
            if fb_model is None:
                logger.error(
                    "push_to_firebase could not find %s in Firebase during update",
                    model_obj._meta.label,
                    extra=log_extra({"model_obj_id": model_obj.pk}),
                )
                raise InvalidObjectPushException
            handle_object_update_on_firebase(model_obj, model_ref)
    except InvalidObjectPushException:
        model_obj.update_firebase_push_status(FirebasePushStatusEnum.FAILED)
    except Exception:
        logger.error(
            "push_to_firebase failed",
            extra=log_extra({"model_obj_id": model_obj.pk}),
            exc_info=True,
        )
        model_obj.update_firebase_push_status(FirebasePushStatusEnum.FAILED)
    else:
        model_obj.update_firebase_push_status(FirebasePushStatusEnum.SUCCESS)

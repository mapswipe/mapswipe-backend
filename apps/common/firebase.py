import abc
import logging
import typing

from firebase_admin.db import Reference as FbReference

from apps.common.models import FirebasePushResource, FirebasePushStatusEnum
from main.celery import app
from main.config import Config

logger = logging.getLogger(__name__)


class InvalidObjectPushException(Exception): ...


class FirebasePush[T: FirebasePushResource](abc.ABC):
    model: type[T]

    def __init__(
        self,
        obj_id: int,
    ):
        self.obj_id = obj_id

    @abc.abstractmethod
    def handle_new_object_on_firebase(self, model_obj: T, fb_reference: FbReference): ...

    @abc.abstractmethod
    def handle_object_update_on_firebase(self, model_obj: T, fb_reference: FbReference): ...

    @abc.abstractmethod
    def get_firebase_path(self, firebase_id: str, model: type[T]) -> str: ...

    def push(self) -> None:
        model_obj = self.model.objects.get(id=self.obj_id)

        model_obj.update_firebase_push_status(FirebasePushStatusEnum.PROCESSING)

        try:
            model_ref = Config.FIREBASE_HELPER.ref(
                self.get_firebase_path(model_obj.firebase_id, self.model),
            )
            fb_model: typing.Any = model_ref.get()

            if not model_obj.firebase_last_pushed:
                if fb_model is not None:
                    logger.error(
                        "Firebase creation error: existing %s found",
                        model_obj._meta.label,
                        extra={"model_obj_id": model_obj.pk},
                    )
                    raise InvalidObjectPushException
                self.handle_new_object_on_firebase(model_obj, model_ref)
            else:
                if fb_model is None:
                    logger.error(
                        "Firebase update error: missing %s in Firebase",
                        model_obj._meta.label,
                        extra={"model_obj_id": model_obj.pk},
                    )
                    raise InvalidObjectPushException
                self.handle_object_update_on_firebase(model_obj, model_ref)

        except InvalidObjectPushException:
            model_obj.update_firebase_push_status(FirebasePushStatusEnum.FAILED)
        except Exception:
            logger.error(
                "Unexpected error while pushing to Firebase",
                extra={"model_obj_id": model_obj.pk},
                exc_info=True,
            )
            model_obj.update_firebase_push_status(FirebasePushStatusEnum.FAILED)
        else:
            model_obj.update_firebase_push_status(FirebasePushStatusEnum.SUCCESS)

    # FIXME: Implement init subclass to check if abstract methods are implemented on subclasses
    @staticmethod
    @abc.abstractmethod
    @app.task()
    def task(obj_id: int) -> None:
        """
        if you define this func in multiple classes in the same file celery will always use the first one
        """
        ...

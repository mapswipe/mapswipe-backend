import abc
import logging
import typing

from firebase_admin.db import Reference as FbReference
from pydantic import BaseModel, ConfigDict

from apps.common.models import FirebasePushResource, FirebasePushStatusEnum
from main.celery import app
from main.config import Config

logger = logging.getLogger(__name__)


class InvalidObjectPushException(Exception): ...


# FIXME(tnagorra): Add inheritance_checks for model and firebase_model
class FirebasePush[T: FirebasePushResource, K: BaseModel](abc.ABC):
    model_class: type[T]
    firebase_model_class: type[K]

    def __init__(
        self,
        obj_id: int,
    ):
        self.obj_id = obj_id

    @classmethod
    def _inheritance_checks(cls):
        # FIXME(tnagorra): Find a better way to skip for base classes
        if cls.__name__ == "FirebasePush":
            # Skip check for the abstract class
            return

        missing_fields = []
        for attr_name in [
            "model_class",
            "firebase_model_class",
        ]:
            if getattr(cls, attr_name, None) is None:
                missing_fields.append(attr_name)

        if missing_fields:
            raise NotImplementedError(f"Please define {','.join(missing_fields)} for {cls}")

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._inheritance_checks()

    @abc.abstractmethod
    def handle_new_object_on_firebase(self, model_obj: T, fb_reference: FbReference): ...

    @abc.abstractmethod
    def handle_object_update_on_firebase(self, model_obj: T, fb_obj: K, fb_reference: FbReference): ...

    @abc.abstractmethod
    def get_firebase_path(self, firebase_id: str, model: type[T]) -> str: ...

    def push(self) -> None:
        model_obj = self.model_class.objects.get(id=self.obj_id)

        # FIXME(tnagorra): The following fails because set firebase_push_status is not set on create/update
        # if model_obj.firebase_push_status_enum != FirebasePushStatusEnum.PENDING:
        #     logger.warning(
        #         "Firebase push error: push is not required for %s",
        #         model_obj._meta.label,
        #         extra={"id": model_obj.pk},
        #     )
        #     return

        model_obj.update_firebase_push_status(FirebasePushStatusEnum.PROCESSING)

        try:
            model_ref = Config.FIREBASE_HELPER.ref(
                self.get_firebase_path(model_obj.firebase_id, self.model_class),
            )
            fb_model: typing.Any = model_ref.get()

            if not model_obj.firebase_last_pushed:
                if fb_model is not None:
                    logger.error(
                        "Firebase create error: %s already exists in Firebase",
                        model_obj._meta.label,
                        extra={"id": model_obj.pk},
                    )
                    raise InvalidObjectPushException
                self.handle_new_object_on_firebase(model_obj, model_ref)
            else:
                if fb_model is None:
                    logger.error(
                        "Firebase update error: missing %s in Firebase",
                        model_obj._meta.label,
                        extra={"id": model_obj.pk},
                    )
                    raise InvalidObjectPushException

                class RelaxedModel(self.firebase_model_class):
                    model_config = ConfigDict(extra="ignore")

                # NOTE: we want to ignore extra fields from firebase
                valid_fb_model = RelaxedModel.model_validate(obj=fb_model)
                valid_fb_model = self.firebase_model_class.model_validate(valid_fb_model)

                self.handle_object_update_on_firebase(model_obj, valid_fb_model, model_ref)
        except InvalidObjectPushException:
            model_obj.update_firebase_push_status(FirebasePushStatusEnum.FAILED)
        except Exception:
            logger.error(
                "Firebase push error: Unexpected error occurred",
                extra={"id": model_obj.pk},
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

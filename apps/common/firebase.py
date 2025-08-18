import abc
import logging
import typing

from firebase_admin.db import Reference as FbReference
from pydantic import BaseModel, ConfigDict

from apps.common.models import FirebasePushResource, FirebasePushStatusEnum
from main.celery import app
from main.config import Config
from main.logging import log_extra
from utils.celery import RetryableTask

logger = logging.getLogger(__name__)


class InvalidObjectPushException(Exception): ...


# FIXME(tnagorra): Add inheritance_checks for model and firebase_model
class FirebasePush[T: FirebasePushResource, K: BaseModel](abc.ABC):
    model_class: type[T]
    firebase_model_class: type[K]
    MAX_RETRY_LIMIT = 3
    MIN_RETRY_DELAY = 30
    MAX_RETRY_DELAY = 60

    def __init__(
        self,
        obj_id: int,
        celery_task: RetryableTask | None = None,
    ):
        self.obj_id = obj_id
        self.celery_task = celery_task

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
                valid_fb_model = self.firebase_model_class.model_validate(obj=valid_fb_model)

                self.handle_object_update_on_firebase(model_obj, valid_fb_model, model_ref)
        except InvalidObjectPushException as exc:
            model_obj.update_firebase_push_status(FirebasePushStatusEnum.FAILED)
            # If in async mode -> retry
            if self.celery_task:
                self.handle_firebase_push_error(
                    exc,
                    self.celery_task,
                    self.model_class,
                    self.MAX_RETRY_LIMIT,
                    self.MIN_RETRY_DELAY,
                    self.MAX_RETRY_DELAY,
                    self.obj_id,
                )
            else:
                # Fallback: schedule async retrigger
                self.retrigger_push.delay(self.obj_id)

        except Exception as exc:
            logger.error(
                "Firebase push error: Unexpected error occurred",
                extra={"id": model_obj.pk},
                exc_info=True,
            )
            model_obj.update_firebase_push_status(FirebasePushStatusEnum.FAILED)
            # If in async mode -> retry
            if self.celery_task:
                self.handle_firebase_push_error(
                    exc,
                    self.celery_task,
                    self.model_class,
                    self.MAX_RETRY_LIMIT,
                    self.MIN_RETRY_DELAY,
                    self.MAX_RETRY_DELAY,
                    self.obj_id,
                )
            else:
                # Fallback: schedule async retrigger
                self.retrigger_push.delay(self.obj_id)
        else:
            model_obj.update_firebase_push_status(FirebasePushStatusEnum.SUCCESS)

    @staticmethod
    def handle_firebase_push_error(
        exc: Exception,
        celery_task: RetryableTask,
        model_class: type[T],
        max_retry_limit: int,
        min_retry_delay: int,
        max_retry_delay: int,
        object_id: int,
    ):
        retries = celery_task.request.retries
        if retries >= max_retry_limit:
            logger.warning("Max push retries reached")
            model_obj = model_class.objects.get(id=object_id)
            model_obj.update_firebase_push_status(FirebasePushStatusEnum.FAILED)
            return

        delay = celery_task.exponential_backoff_with_jitter(
            retries,
            min_delay=min_retry_delay,
            max_delay=max_retry_delay,
        )
        logger.warning(
            f"Retrying push in {delay:.2f} seconds (backoff).",  # noqa: G004
            extra=log_extra({"object_id": object_id}),
            exc_info=True,
        )
        raise celery_task.retry(exc=exc, countdown=delay)

    @staticmethod
    @abc.abstractmethod
    @app.task()
    def retrigger_push(object_id: int) -> None:
        """
        Not NotImplemented due to celery limitation with classmethod. Eg:

        @app.task(bind=True, base=RetryableTask)
        def task(celery_task, object_id):
            ...
            XYZFirebase(self, object_id).push()

        """
        raise NotImplementedError

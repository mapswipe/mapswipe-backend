import abc
import typing
from collections import defaultdict

from django.apps import apps
from django.db import models
from firebase_admin.db import Reference as FbReference


class BaseBulkManager:
    """Keeps track of ORM objects to be action for multiple
    model classes, and automatically creates those objects with `bulk_create`
    when the number of objects accumulated for a given model class exceeds
    `chunk_size`.
    Upon completion of the loop that's `add()`ing objects, the developer must
    call `done()` to ensure the final set of objects is action for all models.
    """

    def __init__(self, chunk_size: int = 100):
        self.chunk_size = chunk_size
        self._queues = defaultdict(list)
        self._summary = defaultdict(int)

    @abc.abstractmethod
    def _commit(self, model_class: type[models.Model]) -> None:
        raise NotImplementedError

    def _process_obj(self, obj: models.Model):
        return obj

    def add(self, *objs: models.Model):
        """Add an object to the queue to be action, and call bulk_create if we
        have enough objs.
        """
        for obj in objs:
            model_class = type(obj)
            model_key = model_class._meta.label
            self._queues[model_key].append(self._process_obj(obj))
            if len(self._queues[model_key]) >= self.chunk_size:
                self._commit(model_class)

    def done(self):
        """Always call this upon completion to make sure the final partial chunk
        is saved.
        """
        for model_name, objs in self._queues.items():
            if len(objs) > 0:
                self._commit(apps.get_model(model_name))

    @abc.abstractmethod
    def summary(self) -> dict[typing.Any, typing.Any]:
        raise NotImplementedError


class BulkCreateManager(BaseBulkManager):
    def __init__(self, chunk_size: int = 100, ignore_conflicts: bool = False):
        super().__init__(chunk_size=chunk_size)
        self.ignore_conflicts = ignore_conflicts

    @typing.override
    def _commit(self, model_class: type[models.Model]):
        model_key = model_class._meta.label
        model_class.objects.bulk_create(
            self._queues[model_key],
            ignore_conflicts=self.ignore_conflicts,
        )
        self._summary[model_key] += len(self._queues[model_key])
        self._queues[model_key] = []

    @typing.override
    def summary(self):
        return {"created": dict(self._summary)}


class BulkUpdateManager(BaseBulkManager):
    def __init__(self, update_fields: list[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_fields = update_fields

    @typing.override
    def _process_obj(self, obj: models.Model):
        if obj.pk is None:
            raise Exception(f"Only object with pk is allowed: {obj}")
        return obj

    @typing.override
    def _commit(self, model_class: type[models.Model]):
        model_key = model_class._meta.label
        model_class.objects.bulk_update(
            self._queues[model_key],
            self.update_fields,
        )
        self._summary[model_key] += len(self._queues[model_key])
        self._queues[model_key] = []

    @typing.override
    def summary(self):
        return {"updated": dict(self._summary)}


# NOTE: Inorder to remove certain item from database, you need to pass `None` as the value of the item.


class BulkManagerSummary(typing.TypedDict):
    count: int


class FirebaseBulkManager[T]:
    def __init__(self, ref: FbReference, chunk_size: int = 150):
        """:param ref: Firebase reference object (Realtime DB)
        :param chunk_size: Number of items to batch before committing
        """
        self.ref = ref
        self.chunk_size = chunk_size
        self._buffer: dict[str, T] = {}
        self._written_count = 0

    def _commit(self) -> None:
        """Commit the current buffer to Firebase and clear the buffer."""
        self.ref.update(self._buffer)
        self._written_count += len(self._buffer)
        self._buffer.clear()

    def add(self, key: str, value: T) -> None:
        """Add a single item to the buffer. When buffer reaches chunk_size, flush it.

        :param key: Firebase node/document ID
        :param value: Data to be written to the Firebase
        """
        self._buffer[key] = value
        if len(self._buffer) >= self.chunk_size:
            self._commit()

    def done(self) -> None:
        """Flush any remaining data in the buffer."""
        if self._buffer:
            self._commit()

    def summary(self) -> BulkManagerSummary:
        """Returns a summary of the number of items written."""
        return {"count": self._written_count}

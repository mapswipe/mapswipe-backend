import datetime

import strawberry
from django.db import models
from django.shortcuts import aget_object_or_404


@strawberry.input
class DateRangeInput:
    from_date: datetime.date
    to_date: datetime.date


@strawberry.input(one_of=True)
class FirebaseOrInternalIdInputType:
    id: strawberry.Maybe[strawberry.ID]
    firebase_id: strawberry.Maybe[strawberry.ID]

    @staticmethod
    async def aget_object_or_404[M: models.Model](
        model: type[M],
        object_id: "FirebaseOrInternalIdInputType",
    ) -> M:
        if object_id.id is not None:
            return await aget_object_or_404(model, id=object_id.id.value)
        if object_id.firebase_id is not None:
            return await aget_object_or_404(model, firebase_id=object_id.firebase_id.value)
        raise Exception("This should never be called")

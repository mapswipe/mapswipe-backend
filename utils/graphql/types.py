import json
import typing
from typing import NewType

import strawberry
from strawberry.scalars import JSON

# generalize all the CustomErrorType
CustomErrorType = strawberry.scalar(
    typing.NewType("CustomErrorType", object),
    description="A generic type to return error messages",
    serialize=lambda v: v,
    parse_value=lambda v: v,
)


@strawberry.type
class MutationResponseType[ResultTypeVar]:
    ok: bool = True
    errors: CustomErrorType | None = None
    result: ResultTypeVar | None = None


@strawberry.input
class DeleteInput:
    id: strawberry.ID


@strawberry.interface
class CudInput[X, Y]:
    create: X | None = strawberry.UNSET
    update: Y | None = strawberry.UNSET
    delete: DeleteInput | None = strawberry.UNSET


AreaSqKm = strawberry.scalar(
    NewType("AreaSqKm", float),
    serialize=lambda v: v,
    parse_value=lambda v: v,
)

GenericJSON = strawberry.scalar(
    NewType("GenericJSON", JSON),
    serialize=lambda v: json.loads(v) if isinstance(v, str) else v,
    parse_value=lambda v: v,
)

import typing

import strawberry

ResultTypeVar = typing.TypeVar("ResultTypeVar")

# generalize all the CustomErrorType
CustomErrorType = strawberry.scalar(
    typing.NewType("CustomErrorType", object),
    description="A generic type to return error messages",
    serialize=lambda v: v,
    parse_value=lambda v: v,
)


@strawberry.type
class MutationResponseType(typing.Generic[ResultTypeVar]):
    ok: bool = True
    errors: typing.Optional[CustomErrorType] = None
    result: typing.Optional[ResultTypeVar] = None

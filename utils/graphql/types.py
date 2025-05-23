import json
import typing
from typing import NewType

import strawberry
import strawberry_django
from django.core.files.storage import FileSystemStorage, default_storage
from django.db import models
from django.db.models.fields import files
from strawberry.scalars import JSON
from strawberry.types import Info
from strawberry_django.fields.types import field_type_map

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


# Replaces strawberry_django.fields.types.DjangoFileType
@strawberry.type
class MapswipeDjangoFileType:
    name: str
    size: int

    @strawberry_django.field
    def url(
        self,
        info: Info,
        file: strawberry.Parent[files.FieldFile],
    ) -> str:
        # TODO: Use cache if using S3 URL with signature
        if isinstance(default_storage, FileSystemStorage):
            return info.context.request.build_absolute_uri(file.url)
        return file.url


field_type_map.update(
    {
        models.FileField: MapswipeDjangoFileType,
    },
)

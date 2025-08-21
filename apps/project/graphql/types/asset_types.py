import strawberry

from utils.asset_types.models import AoiGeometryAssetProperty, ObjectImage, ObjectImageAnnotation, ObjectImageAssetProperty


@strawberry.experimental.pydantic.type(model=AoiGeometryAssetProperty, all_fields=True)
class AoiGeometryAssetPropertyType: ...


@strawberry.experimental.pydantic.type(ObjectImage, all_fields=True)
class ObjectImageType: ...


@strawberry.experimental.pydantic.type(ObjectImageAnnotation, all_fields=True)
class ObjectImageAnnotationType: ...


@strawberry.experimental.pydantic.type(model=ObjectImageAssetProperty, all_fields=True)
class ObjectImageAssetPropertyType: ...

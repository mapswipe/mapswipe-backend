import strawberry

from utils.asset_types.models import ObjectImage, ObjectImageAnnotation, ObjectImageAssetProperty


@strawberry.experimental.pydantic.input(ObjectImage, all_fields=True)
class ObjectImageInput: ...


@strawberry.experimental.pydantic.input(ObjectImageAnnotation, all_fields=True)
class ObjectImageAnnotationInput: ...


@strawberry.experimental.pydantic.input(ObjectImageAssetProperty, all_fields=True)
class ObjectImageAssetPropertyInput: ...

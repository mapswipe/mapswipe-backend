import datetime

from pydantic import BaseModel

from utils import fields as custom_fields


class AoiGeometryAssetProperty(BaseModel):
    bbox: tuple[
        custom_fields.PydanticLng,
        custom_fields.PydanticLng,
        custom_fields.PydanticLat,
        custom_fields.PydanticLng,
    ]
    center: tuple[
        custom_fields.PydanticLng,
        custom_fields.PydanticLat,
    ]
    # NOTE: The area is in square meter. Multiply by 10^4 to get square kilometer.
    area: custom_fields.PydanticPositiveFloat


class ObjectImage(BaseModel):
    id: custom_fields.PydanticPositiveInt
    file_name: str
    license: custom_fields.PydanticPositiveInt | None = None
    coco_url: custom_fields.PydanticUrl | None = None
    flickr_url: custom_fields.PydanticUrl | None = None
    width: custom_fields.PydanticPositiveInt | None = None
    height: custom_fields.PydanticPositiveInt | None = None
    date_captured: datetime.datetime | None = None


class ObjectImageAnnotation(BaseModel):
    # NOTE: `id` is not required in coco format but we might need this to be required
    id: custom_fields.PydanticPositiveInt
    image_id: custom_fields.PydanticPositiveInt
    category_id: custom_fields.PydanticPositiveInt | None = None
    iscrowd: custom_fields.PydanticPositiveInt | None = None
    segmentation: list[list[float]] | None = None
    area: custom_fields.PydanticPositiveFloat | None = None
    bbox: tuple[float, float, float, float]


class ObjectImageAssetProperty(BaseModel):
    image: ObjectImage
    # NOTE: We have not added categories, info and licenses
    annotations: list[ObjectImageAnnotation] | None = None

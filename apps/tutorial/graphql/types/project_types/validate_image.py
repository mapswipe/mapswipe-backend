import strawberry

from project_types.validate_image import tutorial as validate_image_tutorial


@strawberry.experimental.pydantic.type(model=validate_image_tutorial.ValidateImageTutorialTaskProperty, all_fields=True)
class ValidateImageTutorialTaskPropertyType: ...

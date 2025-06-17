import strawberry

from project_types.validate_image import project as validate_image_project


# FIXME(tnagorra): Add one_of here?
@strawberry.experimental.pydantic.input(model=validate_image_project.ValidateImageProjectProperty, all_fields=True)
class ValidateImageProjectPropertyInput: ...

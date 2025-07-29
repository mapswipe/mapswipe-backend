import strawberry
import strawberry_django
from strawberry.file_uploads import Upload

from apps.common.graphql.inputs import (
    ArchivableResourceInputMixin,
    UserResourceCreateInputMixin,
    UserResourceTopLevelUpdateInputMixin,
)
from apps.project.models import Organization, Project, ProjectAsset

# NOTE: We are importing base for side-effect
# The tile server inputs are required by the following imports
from .project_types import base  # noqa: F401  # isort: skip # type: ignore[reportUnusedImport]

from .project_types.compare import CompareProjectPropertyInput
from .project_types.completeness import CompletenessProjectPropertyInput
from .project_types.find import FindProjectPropertyInput
from .project_types.validate import ValidateProjectPropertyInput
from .project_types.validate_image import ValidateImageProjectPropertyInput


# Organization
@strawberry_django.input(Organization)
class OrganizationCreateInput(UserResourceCreateInputMixin):
    name: strawberry.auto
    description: strawberry.auto
    abbreviation: strawberry.auto


@strawberry_django.partial(Organization)
class OrganizationUpdateInput(UserResourceTopLevelUpdateInputMixin, ArchivableResourceInputMixin):
    name: strawberry.auto
    description: strawberry.auto
    abbreviation: strawberry.auto


# Project Properties
@strawberry.input(one_of=True)
class ProjectTypeSpecificInput:
    compare: CompareProjectPropertyInput | None = strawberry.UNSET
    find: FindProjectPropertyInput | None = strawberry.UNSET
    completeness: CompletenessProjectPropertyInput | None = strawberry.UNSET
    validate: ValidateProjectPropertyInput | None = strawberry.UNSET
    validate_image: ValidateImageProjectPropertyInput | None = strawberry.UNSET


# NOTE: Make sure this matches with the serializers ../serializers.py
@strawberry_django.input(Project)
class ProjectCreateInput(UserResourceCreateInputMixin):
    topic: strawberry.auto
    region: strawberry.auto
    project_number: strawberry.auto
    project_type: strawberry.auto
    requesting_organization: strawberry.ID
    look_for: strawberry.auto
    additional_info_url: strawberry.auto
    description: strawberry.auto
    team: strawberry.ID | None = strawberry.UNSET


# NOTE: Make sure this matches with the serializers ../serializers.py
@strawberry_django.partial(Project)
class ProjectUpdateInput(UserResourceTopLevelUpdateInputMixin):
    topic: strawberry.auto
    region: strawberry.auto
    project_number: strawberry.auto
    look_for: strawberry.auto
    additional_info_url: strawberry.auto
    description: strawberry.auto
    verification_number: strawberry.auto
    group_size: strawberry.auto
    max_tasks_per_user: strawberry.auto
    status: strawberry.auto
    tutorial: strawberry.ID | None = strawberry.UNSET
    requesting_organization: strawberry.ID | None = strawberry.UNSET
    image: strawberry.ID | None = strawberry.UNSET
    project_type_specifics: ProjectTypeSpecificInput | None = strawberry.UNSET
    team: strawberry.ID | None = strawberry.UNSET


# NOTE: Make sure this matches with the serializers ../serializers.py
@strawberry_django.partial(Project)
class ProcessedProjectUpdateInput(UserResourceTopLevelUpdateInputMixin):
    topic: strawberry.auto
    region: strawberry.auto
    project_number: strawberry.auto
    look_for: strawberry.auto
    additional_info_url: strawberry.auto
    description: strawberry.auto
    status: strawberry.auto
    tutorial: strawberry.ID | None = strawberry.UNSET
    requesting_organization: strawberry.ID | None = strawberry.UNSET
    image: strawberry.ID | None = strawberry.UNSET
    team: strawberry.ID | None = strawberry.UNSET


# NOTE: Make sure this matches with the serializers ../serializers.py
@strawberry_django.input(ProjectAsset)
class ProjectAssetCreateInput(UserResourceCreateInputMixin):
    mimetype: strawberry.auto
    file: Upload
    project: strawberry.ID

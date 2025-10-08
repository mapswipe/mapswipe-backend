import strawberry
import strawberry_django
from strawberry.file_uploads import Upload

from apps.common.graphql.inputs import (
    ArchivableResourceInputMixin,
    UserResourceCreateInputMixin,
    UserResourceTopLevelUpdateInputMixin,
)
from apps.project.models import Organization, Project, ProjectAsset, ProjectAssetInputTypeEnum, ProjectTypeEnum

from .asset_types import ObjectImageAssetPropertyInput

# NOTE: We are importing base for side-effect
# The tile server inputs are required by the following imports
from .project_types import base  # noqa: F401  # isort: skip # type: ignore[reportUnusedImport]

from .project_types.compare import CompareProjectPropertyInput
from .project_types.completeness import CompletenessProjectPropertyInput
from .project_types.find import FindProjectPropertyInput
from .project_types.street import StreetProjectPropertyInput
from .project_types.validate import ValidateProjectPropertyInput
from .project_types.validate_image import ValidateImageProjectPropertyInput


# Asset
@strawberry.input(one_of=True)
class AssetTypeSpecificInput:
    object_image: ObjectImageAssetPropertyInput | None = strawberry.UNSET


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
    street: StreetProjectPropertyInput | None = strawberry.UNSET


# NOTE: Make sure this matches with the serializers ../serializers.py
@strawberry_django.input(Project)
class ProjectCreateInput(UserResourceCreateInputMixin):
    topic: strawberry.auto
    region: strawberry.auto
    project_number: strawberry.auto
    project_type: strawberry.auto
    requesting_organization: strawberry.ID
    look_for: strawberry.auto
    project_instruction: str
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
    project_instruction: strawberry.auto
    additional_info_url: strawberry.auto
    description: strawberry.auto
    verification_number: strawberry.auto
    group_size: strawberry.auto
    max_tasks_per_user: strawberry.auto
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
    project_instruction: strawberry.auto
    additional_info_url: strawberry.auto
    is_featured: strawberry.auto
    description: strawberry.auto
    max_tasks_per_user: strawberry.auto
    tutorial: strawberry.ID | None = strawberry.UNSET
    requesting_organization: strawberry.ID | None = strawberry.UNSET
    image: strawberry.ID | None = strawberry.UNSET
    team: strawberry.ID | None = strawberry.UNSET


@strawberry_django.partial(Project)
class ProjectStatusUpdateInput(UserResourceTopLevelUpdateInputMixin):
    status: strawberry.auto


# NOTE: Make sure this matches with the serializers ../serializers.py
@strawberry_django.input(ProjectAsset)
class ProjectAssetCreateInput(UserResourceCreateInputMixin):
    project: strawberry.ID
    input_type: ProjectAssetInputTypeEnum
    external_url: strawberry.auto
    file: Upload | None = strawberry.UNSET
    asset_type_specifics: AssetTypeSpecificInput | None = strawberry.UNSET


@strawberry.input
class ProjectNameInput:
    project_type: ProjectTypeEnum
    requesting_organization_id: strawberry.ID
    topic: str
    region: str
    project_number: int

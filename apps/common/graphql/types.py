import datetime

import strawberry

from apps.user.graphql.types import UserType


# -- Interfaces
@strawberry.interface
class UserResourceTypeMixin:
    client_id: str
    created_at: datetime.datetime
    modified_at: datetime.datetime

    created_by: UserType
    modified_by: UserType


@strawberry.type
class ArchivableResourceTypeMixin:
    is_archived: bool
    archived_at: datetime.datetime | None
    archived_by: UserType | None


@strawberry.type
class CommonAssetTypeMixin:
    type: strawberry.auto
    file_size: strawberry.auto
    mimetype: strawberry.auto
    marked_as_deleted: strawberry.auto

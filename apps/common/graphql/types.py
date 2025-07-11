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
    is_archived: bool | None
    archived_at: datetime.datetime | None
    archived_by: UserType | None

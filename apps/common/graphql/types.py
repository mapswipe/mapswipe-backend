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

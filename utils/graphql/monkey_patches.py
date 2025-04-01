from typing import TYPE_CHECKING

import strawberry_django.mutations.resolvers
from strawberry_django.mutations.resolvers import prepare_create_update

if TYPE_CHECKING:
    from main.graphql.context import Info


def custom_prepare_create_update(*args, **kwargs):
    info: Info = kwargs["info"]
    user_id = info.context.request.user.pk
    resp_instance, resp_direct_field_values, resp_m2m = prepare_create_update(*args, **kwargs)
    has_created_by = hasattr(resp_instance, "created_by_id")
    has_modified_by = hasattr(resp_instance, "modified_by_id")
    # Create
    if has_created_by and resp_instance.pk is None:
        resp_direct_field_values["created_by_id"] = user_id
        resp_instance.created_by_id = user_id  # type: ignore[reportAttributeAccessIssue]
    # Update
    if has_modified_by:
        resp_direct_field_values["modified_by_id"] = user_id
        resp_instance.modified_by_id = user_id  # type: ignore[reportAttributeAccessIssue]
    return resp_instance, resp_direct_field_values, resp_m2m


strawberry_django.mutations.resolvers.prepare_create_update = custom_prepare_create_update

import strawberry


@strawberry.input
class UserResourceCreateInputMixin:
    client_id: str


@strawberry.input
class UserResourceUpdateInputMixin:
    id: strawberry.ID
    client_id: str


@strawberry.input
class UserResourceTopLevelUpdateInputMixin:
    client_id: str


@strawberry.input
class ArchivableResourceInputMixin:
    is_archived: bool | None = strawberry.UNSET

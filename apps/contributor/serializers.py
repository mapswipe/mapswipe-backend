import typing

from django.db import transaction

from apps.common.models import FirebasePushStatusEnum
from apps.common.serializers import ArchivableResourceSerializer, UserResourceSerializer
from apps.contributor.firebase import FirebaseContributorUserGroup

from .models import ContributorUserGroup


class ContributorUserGroupSerializer(
    UserResourceSerializer[ContributorUserGroup],
    ArchivableResourceSerializer[ContributorUserGroup],
):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = ContributorUserGroup
        fields = (
            "name",
            "description",
            "is_archived",
        )

    @typing.override
    def create(self, validated_data: dict[str, typing.Any]) -> ContributorUserGroup:
        user_group = super().create(validated_data)
        user_group.update_firebase_push_status(FirebasePushStatusEnum.PENDING)
        transaction.on_commit(lambda: FirebaseContributorUserGroup(user_group.id).push())
        return user_group

    @typing.override
    def update(self, instance: ContributorUserGroup, validated_data: dict[typing.Any, typing.Any]):
        user_group = super().update(instance, validated_data)
        user_group.update_firebase_push_status(FirebasePushStatusEnum.PENDING)
        transaction.on_commit(lambda: FirebaseContributorUserGroup(user_group.id).push())
        return user_group

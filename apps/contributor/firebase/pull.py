import datetime
import logging

from django.db import connection, transaction
from pyfirebase_mapswipe import extended_models as firebase_ext_models
from pyfirebase_mapswipe import models as firebase_models

from apps.contributor.models import (
    ContributorUser,
    ContributorUserGroupMembershipLogActionEnum,
    ContributorUserGroupMembershipLogTemp,
)
from main.bulk_managers import BulkCreateManager
from main.config import Config
from utils.common import tb_name

from .sql import (
    SQL_QUERY_TO_PRE_FILL_TEMP_TABLE_DATA_REF_COLUMNS,
    SQL_QUERY_TO_TRANSFER_TEMP_TABLE_DATA_TO_USER_GROUP_MEMBERSHIP_LOGS,
    SQL_QUERY_TO_TRANSFER_TEMP_TABLE_DATA_TO_USER_GROUP_MEMBERSHIPS,
    SQL_QUERY_TO_UPDATE_USER_GROUP_MEMBERSHIPS,
)
from .utils import get_list_of_items_from_firebase

logger = logging.getLogger(__name__)


def pull_users_from_firebase():
    valid_users, errored_users_count, user_updates_ref = get_list_of_items_from_firebase(
        firebase_ext_models.FbUser,
        Config.FirebaseKeys.contributor_user_updates(),
        Config.FirebaseKeys.contributor_user,
    )
    if len(valid_users) <= 0 and errored_users_count <= 0:
        return True

    users_to_pull = list[ContributorUser]()
    for key, valid_user in valid_users:
        user = ContributorUser(
            firebase_id=key,
            username=valid_user.username,
            created_at=valid_user.created,
            modified_at=valid_user.created,
        )
        users_to_pull.append(user)

    prev_users_count = ContributorUser.objects.count()
    ContributorUser.objects.bulk_create(
        users_to_pull,
        update_conflicts=True,
        update_fields=["username"],
        unique_fields=["firebase_id"],
    )
    curr_users_count = ContributorUser.objects.count()

    created_users_count = curr_users_count - prev_users_count
    updated_users_count = len(users_to_pull) - created_users_count
    logger.info("%s contributor users created.", created_users_count)
    logger.info("%s contributor users updated.", updated_users_count)
    logger.info("%s contributor users not pulled.", errored_users_count)

    if len(users_to_pull) > 0:
        user_updates_ref.update({user.firebase_id: None for user in users_to_pull})
    return True


def pull_user_group_memberships_from_firebase():
    valid_membership_logs, errored_membership_logs_count, membership_logs_ref = get_list_of_items_from_firebase(
        firebase_models.FbUserGroupMembership,
        Config.FirebaseKeys.user_group_membership_log_updates(),
        Config.FirebaseKeys.user_group_membership_log,
    )

    # FIXME(tnagorra): Do we need to move this to transaction block?
    bulk_create_manager = BulkCreateManager()
    for key, valid_membership_log in valid_membership_logs:
        membership_log = ContributorUserGroupMembershipLogTemp(
            firebase_id=key,
            contributor_user_group_firebase_id=valid_membership_log.userGroupId,
            contributor_user_firebase_id=valid_membership_log.userId,
            date=datetime.datetime.fromtimestamp(int(valid_membership_log.timestamp / 1000)),
            action=ContributorUserGroupMembershipLogActionEnum.from_firebase(valid_membership_log.action),
        )
        bulk_create_manager.add(membership_log)
    bulk_create_manager.done()

    with transaction.atomic(), connection.cursor() as cursor:
        logger.info("Processing user group membership logs temp table data")
        cursor.execute(SQL_QUERY_TO_PRE_FILL_TEMP_TABLE_DATA_REF_COLUMNS)

        logger.info("Transferring staging user group membership logs to real tables")
        logger.info("Creating user group memberships")
        cursor.execute(SQL_QUERY_TO_TRANSFER_TEMP_TABLE_DATA_TO_USER_GROUP_MEMBERSHIPS)
        logger.info("Creating user group membership logs")
        cursor.execute(SQL_QUERY_TO_TRANSFER_TEMP_TABLE_DATA_TO_USER_GROUP_MEMBERSHIP_LOGS)
        logger.info("Updating user group memberships from membership logs")
        cursor.execute(SQL_QUERY_TO_UPDATE_USER_GROUP_MEMBERSHIPS)
        logger.info("Transferred staging user group membership logs to real tables")

        valid_user_group_membership_logs_temp_qs = (
            ContributorUserGroupMembershipLogTemp.objects.filter(is_firebase_mapping_valid=True)
            .values_list("firebase_id", flat=True)
            .distinct()
        )
        processed_membership_logs = list(valid_user_group_membership_logs_temp_qs)

        logger.info("Cleaning up staging user group membership logs")
        cursor.execute(f"TRUNCATE TABLE {tb_name(ContributorUserGroupMembershipLogTemp)} RESTART IDENTITY;")
        logger.info("Cleared staging user group membership logs")

    logger.info("%s user group membership logs created.", len(processed_membership_logs))
    logger.info(
        "%s user group membership logs not pulled.",
        errored_membership_logs_count + (len(valid_membership_logs) - len(processed_membership_logs)),
    )
    if len(processed_membership_logs) > 0:
        val = {firebase_id: None for firebase_id in processed_membership_logs}
        membership_logs_ref.update(val)

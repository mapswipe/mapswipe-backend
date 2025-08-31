import logging

from apps.contributor.models import (
    ContributorUser,
    ContributorUserGroup,
    ContributorUserGroupMembership,
    ContributorUserGroupMembershipLog,
    ContributorUserGroupMembershipLogActionEnum,
    ContributorUserGroupMembershipLogTemp,
)
from utils.common import fd_name, tb_name

logger = logging.getLogger(__name__)

SQL_QUERY_TO_PRE_FILL_TEMP_TABLE_DATA_REF_COLUMNS = f"""
    WITH processed AS (
        SELECT
            MLT.{fd_name(ContributorUserGroupMembershipLogTemp.id)} as membership_log_id,
            -- Ref
            CU.{fd_name(ContributorUser.id)} as contributor_user_id,
            CUG.{fd_name(ContributorUserGroup.id)} as contributor_user_group_id
        FROM
            {tb_name(ContributorUserGroupMembershipLogTemp)} MLT
                -- Contributor User
                LEFT JOIN {tb_name(ContributorUser)} CU ON
                    CU.{fd_name(ContributorUser.firebase_id)} = MLT.{fd_name(ContributorUserGroupMembershipLogTemp.contributor_user_firebase_id)}
                -- Contributor User Group
                LEFT JOIN {tb_name(ContributorUserGroup)} CUG ON
                    CUG.{fd_name(ContributorUserGroup.firebase_id)} = MLT.{fd_name(ContributorUserGroupMembershipLogTemp.contributor_user_group_firebase_id)}
    )
    UPDATE {tb_name(ContributorUserGroupMembershipLogTemp)}
    SET
        {fd_name(ContributorUserGroupMembershipLogTemp.contributor_user_id)} = processed.contributor_user_id,
        {fd_name(ContributorUserGroupMembershipLogTemp.contributor_user_group_id)} = processed.contributor_user_group_id,
        {fd_name(ContributorUserGroupMembershipLogTemp.is_firebase_mapping_valid)} = (
            processed.contributor_user_id is not NULL
            AND processed.contributor_user_group_id is not NULL
        )
    FROM processed
    WHERE
        {tb_name(ContributorUserGroupMembershipLogTemp)}.{fd_name(ContributorUserGroupMembershipLogTemp.id)} = processed.membership_log_id;
"""  # noqa: E501

SQL_QUERY_TO_TRANSFER_TEMP_TABLE_DATA_TO_USER_GROUP_MEMBERSHIPS = f"""
    INSERT INTO {tb_name(ContributorUserGroupMembership)} (
        -- Ref
        {fd_name(ContributorUserGroupMembership.user)},
        {fd_name(ContributorUserGroupMembership.user_group)},
        -- Value
        {fd_name(ContributorUserGroupMembership.is_active)}
    ) (
        SELECT
            MLT.{fd_name(ContributorUserGroupMembershipLogTemp.contributor_user_id)},
            MLT.{fd_name(ContributorUserGroupMembershipLogTemp.contributor_user_group_id)},
            false -- TODO(tnagorra): Check if false or False
        FROM
            {tb_name(ContributorUserGroupMembershipLogTemp)} MLT
        WHERE
            MLT.{fd_name(ContributorUserGroupMembershipLogTemp.is_firebase_mapping_valid)} is True
        GROUP BY
            MLT.{fd_name(ContributorUserGroupMembershipLogTemp.contributor_user_group_id)},
            MLT.{fd_name(ContributorUserGroupMembershipLogTemp.contributor_user_id)}
    )
    ON CONFLICT (
         {fd_name(ContributorUserGroupMembership.user)},
         {fd_name(ContributorUserGroupMembership.user_group)}
    )
    DO NOTHING;
"""


SQL_QUERY_TO_TRANSFER_TEMP_TABLE_DATA_TO_USER_GROUP_MEMBERSHIP_LOGS = f"""
    INSERT INTO {tb_name(ContributorUserGroupMembershipLog)} (
        -- Ref
        {fd_name(ContributorUserGroupMembershipLog.membership)},
        -- Value
        {fd_name(ContributorUserGroupMembershipLog.date)},
        {fd_name(ContributorUserGroupMembershipLog.action)}
    ) (
        SELECT
            CUGM.{fd_name(ContributorUserGroupMembership.id)},
            MLT.{fd_name(ContributorUserGroupMembershipLogTemp.date)},
            MLT.{fd_name(ContributorUserGroupMembershipLogTemp.action)}
        FROM
            {tb_name(ContributorUserGroupMembershipLogTemp)} MLT
                -- Contributor User Group Membership
                LEFT JOIN {tb_name(ContributorUserGroupMembership)} CUGM ON
                    CUGM.{fd_name(ContributorUserGroupMembership.user_id)} = MLT.{fd_name(ContributorUserGroupMembershipLogTemp.contributor_user_id)}
                    AND CUGM.{fd_name(ContributorUserGroupMembership.user_group_id)} = MLT.{fd_name(ContributorUserGroupMembershipLogTemp.contributor_user_group_id)}
        WHERE
            MLT.{fd_name(ContributorUserGroupMembershipLogTemp.is_firebase_mapping_valid)} is True
    );
"""  # noqa: E501

SQL_QUERY_TO_UPDATE_USER_GROUP_MEMBERSHIPS = f"""
    WITH filter AS (
        SELECT
            MIN(MLT.{fd_name(ContributorUserGroupMembershipLogTemp.date)}) as min_date
        FROM
            {tb_name(ContributorUserGroupMembershipLogTemp)} MLT
    ),
    latest_membership AS (
        SELECT
            DISTINCT ON (ML.{fd_name(ContributorUserGroupMembershipLog.membership)})
            ML.{fd_name(ContributorUserGroupMembershipLog.membership)} AS membership_id,
            ML.{fd_name(ContributorUserGroupMembershipLog.action)} AS action
        FROM
            {tb_name(ContributorUserGroupMembershipLog)} ML
        WHERE
            ML.{fd_name(ContributorUserGroupMembershipLog.date)} >= (select min_date from filter)
        ORDER BY
            ML.{fd_name(ContributorUserGroupMembershipLog.membership)},
            ML.{fd_name(ContributorUserGroupMembershipLog.date)} DESC
    )
    UPDATE {tb_name(ContributorUserGroupMembership)}
    SET
        {fd_name(ContributorUserGroupMembership.is_active)} = (latest_membership.action = {ContributorUserGroupMembershipLogActionEnum.JOIN.value})
    FROM
        latest_membership
    WHERE
        {tb_name(ContributorUserGroupMembership)}.{fd_name(ContributorUserGroupMembership.id)} = latest_membership.membership_id;
"""  # noqa: E501

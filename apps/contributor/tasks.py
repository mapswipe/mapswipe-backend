import logging
import typing

from celery import shared_task
from pydantic import ValidationError
from pyfirebase_mapswipe import extended_models as firebase_ext_models

from apps.contributor.models import ContributorUser
from main.cache import CeleryLock
from main.config import Config

logger = logging.getLogger(__name__)


@shared_task
def pull_users_from_firebase():
    with CeleryLock.redis_lock(CeleryLock.Key.USERS_PULL_FROM_FIREBASE) as acquired:
        if not acquired:
            logger.warning("Pull users from firebase is already running")
            return None

    try:
        contributor_user_updates_ref = Config.FIREBASE_HELPER.ref(Config.FirebaseKeys.contributor_user_updates())

        contributor_user_keys = typing.cast("dict[str, bool] | None", contributor_user_updates_ref.get())

        # Check if there are any updates
        if not contributor_user_keys:
            logger.info("Pull users from firebase found no updates")
            return True

        all_user_ids = contributor_user_keys.keys()
        errored_users_count = 0

        users_to_pull = list[ContributorUser]()
        for user_id in all_user_ids:
            user_ref = Config.FIREBASE_HELPER.ref(Config.FirebaseKeys.contributor_user(user_id))
            try:
                user = typing.cast("dict[str, typing.Any] | None", user_ref.get())
                if not user:
                    raise LookupError(f"User with key {user_id} not found")
                user_obj = firebase_ext_models.FbUser(**user)
            except ValidationError:
                errored_users_count += 1
                logger.warning("Validation failed for user from firebase: %s", user_id)
                continue
            except LookupError:
                errored_users_count += 1
                logger.warning("User not found in firebase: %s", user_id)
                continue

            user = ContributorUser(
                firebase_id=user_id,
                username=user_obj.username,
                created_at=user_obj.created,
                modified_at=user_obj.created,
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

        contributor_user_updates_ref.update({user.firebase_id: None for user in users_to_pull})
        return True
    except Exception:
        logger.error("Pull users from firebase failed", exc_info=True)
        return False

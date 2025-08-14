import logging
import typing

from celery import shared_task
from django.utils import timezone
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
            return True

        all_user_ids = set(contributor_user_keys.keys())
        processed_user_ids = set[str]()
        errored_user_ids = set[str]()

        users_to_update: list[ContributorUser] = []
        db_users = ContributorUser.objects.filter(firebase_id__in=all_user_ids)
        for db_user in db_users.iterator():
            key = db_user.firebase_id

            try:
                user_ref = Config.FIREBASE_HELPER.ref(Config.FirebaseKeys.contributor_user(key))
                updated_user = typing.cast("dict[str, typing.Any] | None", user_ref.get())
                if not updated_user:
                    raise LookupError(f"User with key {key} not found")
                updated_user_obj = firebase_ext_models.FbUser(**updated_user)
            except (ValidationError, LookupError):
                # TODO(tnagorra): Do we need to log errors?
                errored_user_ids.add(key)
                continue

            # TODO(tnagorra): Add last_synced_time?
            db_user.username = updated_user_obj.username
            db_user.modified_at = timezone.now()

            processed_user_ids.add(key)
            users_to_update.append(db_user)

        other_user_ids = all_user_ids - processed_user_ids - errored_user_ids

        users_to_create: list[ContributorUser] = []
        for key in other_user_ids:
            user_ref = Config.FIREBASE_HELPER.ref(Config.FirebaseKeys.contributor_user(key))
            try:
                created_user = typing.cast("dict[str, typing.Any] | None", user_ref.get())
                if not created_user:
                    raise LookupError(f"User with key {key} not found")
                created_user_obj = firebase_ext_models.FbUser(**created_user)
            except (ValidationError, LookupError):
                # TODO(tnagorra): Do we need to log errors?
                errored_user_ids.add(key)
                continue

            new_user = ContributorUser(
                firebase_id=key,
                username=created_user_obj.username,
                created_at=created_user_obj.created,
                modified_at=created_user_obj.created,
            )
            processed_user_ids.add(key)
            users_to_create.append(new_user)

        if len(users_to_update) > 0:
            ContributorUser.objects.bulk_update(
                users_to_update,
                ["username"],
            )
            logger.info("%s contributor users updated.", len(users_to_update))
        if len(users_to_create) > 0:
            ContributorUser.objects.bulk_create(
                users_to_create,
            )
            logger.info("%s contributor users created.", len(users_to_create))

        unprocessed_user_ids = len(all_user_ids) - len(processed_user_ids)
        if unprocessed_user_ids > 0:
            logger.info("%s contributor user updates could not be processed.", unprocessed_user_ids)

        # Only clearing out updates that were successful
        contributor_user_updates_ref.update({key: None for key in processed_user_ids})
        return True
    except Exception:
        logger.error("Pull users from firebase failed", exc_info=True)
        return False

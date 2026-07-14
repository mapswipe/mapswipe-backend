import logging
import typing

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q, QuerySet
from firebase_admin import auth  # type: ignore[reportMissingTypeStubs]

from apps.contributor.models import ContributorUser
from main.config import Config

logger = logging.getLogger(__name__)

FH = Config.FIREBASE_HELPER
K = Config.FirebaseKeys

ANONYMIZED_USERNAME = "Deleted User"
ANONYMIZED_USERNAME_KEY = "deleted user"

# The Firebase user node carries the display name in four legacy (dual-written) fields.
# These are the only place a user's name (PII) lives; results/groupsUsers/membershipLogs are
# keyed by uid and carry no name, so anonymisation never needs to fan out. See
# ``docs/firebase_data_flow.md``.
NAME_FIELD_OVERRIDES = {
    "userName": ANONYMIZED_USERNAME,
    "username": ANONYMIZED_USERNAME,
    "userNameKey": ANONYMIZED_USERNAME_KEY,
    "usernameKey": ANONYMIZED_USERNAME_KEY,
}


def osm_access_token_key(firebase_id: str) -> str:
    return f"/v2/OSMAccessToken/{firebase_id}"


def anonymize_user_in_firebase(firebase_id: str, *, dry_run: bool) -> None:
    """Scrub PII from the Firebase user node and drop the OSM access token.

    Keeps all pseudonymous data (contributions, counters, group memberships) intact.
    """
    user_path = K.contributor_user(firebase_id)
    osm_path = osm_access_token_key(firebase_id)

    if dry_run:
        logger.info("[dry-run] would anonymize name fields at %s", user_path)
        logger.info("[dry-run] would delete OSM access token at %s", osm_path)
        return

    user_ref = FH.ref(user_path)
    # Only patch an existing node; ``update`` on a missing path would resurrect it.
    if user_ref.get(shallow=True) is not None:
        user_ref.update(value=NAME_FIELD_OVERRIDES)
        logger.info("Anonymized name fields at %s", user_path)
    else:
        logger.warning("No Firebase user node at %s; skipping name anonymization", user_path)

    FH.ref(osm_path).delete()
    logger.info("Deleted OSM access token at %s", osm_path)


def delete_firebase_auth_user(firebase_id: str, *, dry_run: bool) -> None:
    """Delete the Firebase Auth account (email / OAuth identity). Best effort."""
    if dry_run:
        logger.info("[dry-run] would delete Firebase auth user %s", firebase_id)
        return

    try:
        FH.auth.delete_user(firebase_id)
        logger.info("Deleted Firebase auth user %s", firebase_id)
    except auth.UserNotFoundError:
        logger.warning("No Firebase auth user for %s; nothing to delete", firebase_id)
    except Exception:
        logger.exception("Failed to delete Firebase auth user %s", firebase_id)


def anonymize_user_in_db(user: ContributorUser, *, dry_run: bool) -> None:
    if dry_run:
        logger.info("[dry-run] would set ContributorUser %s username to %r", user.pk, ANONYMIZED_USERNAME)
        return

    user.username = ANONYMIZED_USERNAME
    user.save(update_fields=["username"])
    logger.info("Anonymized ContributorUser %s username in Postgres", user.pk)


class Command(BaseCommand):
    help = (
        "Anonymize a contributor user (GDPR erasure). Scrubs the user's name from Firebase and "
        "Postgres, deletes their OSM access token and Firebase auth account, and leaves all "
        "pseudonymous contribution data (results, group memberships, aggregate counts) intact."
    )

    @typing.override
    def add_arguments(self, parser):  # type: ignore[reportMissingParameterType]
        selection = parser.add_argument_group("user selection")
        selection.add_argument(
            "--user-id",
            dest="user_ids",
            nargs="+",
            type=int,
            help="One or more ContributorUser database ids to anonymize.",
        )
        selection.add_argument(
            "--firebase-id",
            dest="firebase_ids",
            nargs="+",
            help="One or more ContributorUser Firebase ids (uid) to anonymize.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Log what would change without writing anything.",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Skip the confirmation prompt.",
        )

    def _select_users(self, options) -> QuerySet[ContributorUser]:  # type: ignore[reportMissingParameterType]
        user_ids = options["user_ids"]
        firebase_ids = options["firebase_ids"]

        if not user_ids and not firebase_ids:
            raise CommandError("Provide --user-id and/or --firebase-id to select users.")

        query = Q()
        if user_ids:
            query |= Q(pk__in=user_ids)
        if firebase_ids:
            query |= Q(firebase_id__in=firebase_ids)

        return ContributorUser.objects.filter(query).order_by("pk")

    @typing.override
    def handle(self, *args, **options):  # type: ignore[reportMissingParameterType]
        dry_run = options["dry_run"]

        users = list(self._select_users(options))
        if not users:
            self.stdout.write(self.style.WARNING("No contributor users matched the selection."))
            return

        # Warn about firebase-ids that did not resolve to a user.
        requested_firebase_ids = set(options["firebase_ids"] or [])
        found_firebase_ids = {u.firebase_id for u in users}
        for missing in sorted(requested_firebase_ids - found_firebase_ids):
            logger.warning("No ContributorUser found for firebase_id=%s; skipping", missing)

        self.stdout.write(f"Selected {len(users)} user(s) to anonymize:")
        for user in users:
            self.stdout.write(f"  - user_id={user.pk} firebase_id={user.firebase_id} username={user.username!r}")

        if dry_run:
            self.stdout.write(self.style.NOTICE("Dry run: no changes will be made."))
        elif not options["yes"]:
            confirm = input("Proceed with anonymizing these users? [y/N] ").strip().lower()
            if confirm not in ("y", "yes"):
                self.stdout.write(self.style.WARNING("Aborted."))
                return

        for user in users:
            anonymize_user_in_firebase(user.firebase_id, dry_run=dry_run)
            delete_firebase_auth_user(user.firebase_id, dry_run=dry_run)
            anonymize_user_in_db(user, dry_run=dry_run)

        verb = "Would anonymize" if dry_run else "Anonymized"
        self.stdout.write(self.style.SUCCESS(f"{verb} {len(users)} user(s)."))

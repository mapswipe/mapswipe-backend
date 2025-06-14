# pyright: reportMissingTypeStubs=false
import logging

import firebase_admin
from firebase_admin.db import reference as firebase_db_reference

from utils.common import parse_b64gzjson_to_dict

logger = logging.getLogger(__name__)


def get_firebase_app(
    database_url: str,
    credential: firebase_admin.credentials.Certificate | None = None,
    using_emulator: bool = False,
) -> firebase_admin.App:
    try:
        # Is an App instance already initialized?
        return firebase_admin.get_app()
    except ValueError:
        if using_emulator:
            firebase_admin.initialize_app(
                options={
                    "databaseURL": database_url,
                },
            )
            return firebase_admin.get_app()

        firebase_admin.initialize_app(
            credential=credential,
            options={
                "databaseURL": database_url,
            },
        )

        return firebase_admin.get_app()


def _get_firebase_creds(credential_b64_gz: str | None):
    if not credential_b64_gz:
        return None
    service_account_info = parse_b64gzjson_to_dict(credential_b64_gz)
    return firebase_admin.credentials.Certificate(service_account_info)


class FirebaseHelper:
    def __init__(
        self,
        database_url: str,
        credential_b64_gz: str | None = None,
        using_emulator: bool = False,
    ):
        self.app = get_firebase_app(
            database_url,
            credential=_get_firebase_creds(credential_b64_gz),
            using_emulator=using_emulator,
        )
        self.ref = firebase_db_reference("", app=self.app)

# pyright: reportMissingTypeStubs=false
import logging
import typing

import firebase_admin
from firebase_admin.db import reference as firebase_db_reference
from pyfirebase_mapswipe import models as firebase_models

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

    def ref(self, key: str):
        return firebase_db_reference(key, app=self.app)


# TODO(tnagorra): Move this to firebase repo
class FbProject(
    firebase_models.FbProjectCreateOnlyInput,
    firebase_models.FbProjectUpdateInput,
    firebase_models.FbProjectReadonlyType,
):
    class Config:  # type: ignore[reportIncompatibleVariableOverride]
        use_enum_values = True
        extra = "forbid"

    @typing.override
    def __setattr__(self, name: str, value: typing.Any) -> None:
        super(firebase_models.FbProjectReadonlyType).__setattr__(name, value)
        super(firebase_models.FbProjectCreateOnlyInput).__setattr__(name, value)
        super(firebase_models.FbProjectUpdateInput).__setattr__(name, value)

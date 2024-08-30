"""Keyring token storage is NOT used. We used it before this commit but
users who connect to remote machines through passwordless SSH faced some issues."""

import keyring
from medperf import settings


class KeyringTokenStore:
    def __init__(self):
        pass

    def set_tokens(self, account_id, access_token, refresh_token):
        keyring.set_password(
            settings.access_token_storage_id,
            account_id,
            access_token,
        )
        keyring.set_password(
            settings.refresh_token_storage_id,
            account_id,
            refresh_token,
        )

    def read_tokens(self, account_id):
        access_token = keyring.get_password(
            settings.access_token_storage_id,
            account_id,
        )
        refresh_token = keyring.get_password(
            settings.refresh_token_storage_id,
            account_id,
        )
        return access_token, refresh_token

    def delete_tokens(self, account_id):
        keyring.delete_password(
            settings.access_token_storage_id,
            account_id,
        )
        keyring.delete_password(
            settings.refresh_token_storage_id,
            account_id,
        )

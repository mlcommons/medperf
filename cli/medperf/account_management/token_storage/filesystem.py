import os
import base64
from medperf.utils import base_storage_path, remove_path
from medperf import config


class FilesystemTokenStore:
    def __init__(self):
        self.creds_folder = base_storage_path(config.creds_folder)
        os.makedirs(self.creds_folder, exist_ok=True)

    def __get_paths(self, account_id):
        # Base64 encoding is used just to avoid facing a filesystem that doesn't support
        # special characters used in emails.
        account_id_encoded = base64.b64encode(account_id.encode("utf-8")).decode(
            "utf-8"
        )
        account_folder = os.path.join(self.creds_folder, account_id_encoded)
        os.makedirs(account_folder, exist_ok=True)

        access_token_file = os.path.join(account_folder, config.access_token_storage_id)
        refresh_token_file = os.path.join(
            account_folder, config.refresh_token_storage_id
        )

        return access_token_file, refresh_token_file

    def set_tokens(self, account_id, access_token, refresh_token):
        access_token_file, refresh_token_file = self.__get_paths(account_id)

        fd = os.open(access_token_file, os.O_CREAT | os.O_WRONLY, 0o600)
        os.write(fd, access_token.encode("utf-8"))
        os.close(fd)

        fd = os.open(refresh_token_file, os.O_CREAT | os.O_WRONLY, 0o600)
        os.write(fd, refresh_token.encode("utf-8"))
        os.close(fd)

    def read_tokens(self, account_id):
        access_token_file, refresh_token_file = self.__get_paths(account_id)
        with open(access_token_file) as f:
            access_token = f.read()
        with open(refresh_token_file) as f:
            refresh_token = f.read()
        return access_token, refresh_token

    def delete_tokens(self, account_id):
        access_token_file, refresh_token_file = self.__get_paths(account_id)
        remove_path(access_token_file)
        remove_path(refresh_token_file)

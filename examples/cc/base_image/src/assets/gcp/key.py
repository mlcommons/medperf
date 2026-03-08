from google.cloud import kms
from google.cloud import storage

from .utils import GCPAssetConfig, get_credentials


class GCPKey:
    def __init__(self, asset_config_dict: dict):

        asset_config = GCPAssetConfig(**asset_config_dict)
        self.bucket_name = asset_config.bucket
        self.key_name = asset_config.full_key_name
        self.wippro = asset_config.full_wip_name
        self.encrypted_key_path = asset_config.encrypted_key_bucket_file

        self.kms_client = None
        self.storage_client = None

    def __get_encrypted_key(self) -> bytes:
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(self.encrypted_key_path)
        encrypted_key = blob.download_as_bytes()
        return encrypted_key

    def __decrypt_bytes(self, encrypted_data: bytes) -> bytes:
        decrypt_request = kms.DecryptRequest(
            name=self.key_name,
            ciphertext=encrypted_data,
        )
        decrypt_response = self.kms_client.decrypt(request=decrypt_request)
        return decrypt_response.plaintext

    def initialize(self) -> None:
        creds = get_credentials(self.wippro)
        self.kms_client = kms.KeyManagementServiceClient(credentials=creds)
        self.storage_client = storage.Client()

    def get_key(self, output_path: str) -> None:
        encrypted_key = self.__get_encrypted_key()
        key_bytes = self.__decrypt_bytes(encrypted_key)
        with open(output_path, "wb") as f:
            f.write(key_bytes)

from medperf.utils import (
    generate_tmp_path,
    tmp_path_for_cc_asset_key,
    secure_write_to_file,
    get_file_hash,
    remove_path,
)
from medperf.encryption import SymmetricEncryption
from medperf.asset_management.gcp_utils import GCPAssetConfig, upload_file_to_gcs
from medperf.asset_management.asset_check import verify_asset_owner_setup
from medperf.exceptions import MedperfException


class AssetStorageManager:
    def __init__(self, config: dict, asset_path: str, encryption_key: bytes):
        self.config = GCPAssetConfig(**config)

        self.asset_path = asset_path
        self.encryption_key = encryption_key

    def __encrypt_asset(self):
        tmp_encrypted_asset_path = generate_tmp_path()
        encryption_key_file = tmp_path_for_cc_asset_key()
        secure_write_to_file(encryption_key_file, self.encryption_key)
        SymmetricEncryption().encrypt_file(
            self.asset_path, encryption_key_file, tmp_encrypted_asset_path
        )
        remove_path(encryption_key_file, sensitive=True)
        asset_hash = get_file_hash(tmp_encrypted_asset_path)
        return tmp_encrypted_asset_path, asset_hash

    def __upload_encrypted_asset(self, tmp_encrypted_asset_path):
        upload_file_to_gcs(
            self.config,
            tmp_encrypted_asset_path,
            self.config.encrypted_asset_bucket_file,
        )

    def setup(self):
        success, message = verify_asset_owner_setup(
            self.config.bucket, self.config.full_key_name, self.config.full_wip_name
        )
        if not success:
            raise MedperfException(f"Asset owner setup verification failed: {message}")

    def store_asset(self):
        tmp_encrypted_asset_path, asset_hash = self.__encrypt_asset()
        self.__upload_encrypted_asset(tmp_encrypted_asset_path)
        return asset_hash

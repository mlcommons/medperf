from medperf.utils import generate_tmp_path, get_file_hash
from medperf.encryption import SymmetricEncryption
from medperf.asset_management.gcp_utils import GCPAssetConfig, upload_file_to_gcs
from medperf.asset_management.asset_check import verify_asset_owner_setup
from medperf.exceptions import MedperfException


class AssetStorageManager:
    def __init__(self, config: dict, asset_path: str, encryption_key_file: str):
        self.config = GCPAssetConfig(**config)

        self.asset_path = asset_path
        self.encryption_key_file = encryption_key_file

    def __encrypt_asset(self):
        tmp_encrypted_asset_path = generate_tmp_path()
        SymmetricEncryption().encrypt_file(
            self.asset_path, self.encryption_key_file, tmp_encrypted_asset_path
        )
        asset_hash = get_file_hash(tmp_encrypted_asset_path)
        return tmp_encrypted_asset_path, asset_hash

    def __upload_encrypted_asset(self, tmp_encrypted_asset_path):
        upload_file_to_gcs(
            self.config,
            tmp_encrypted_asset_path,
            f"gs://{self.config.bucket}/{self.config.encrypted_asset_bucket_file}",
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

from medperf.utils import generate_tmp_path, get_file_hash
from medperf.encryption import SymmetricEncryption
from medperf.asset_management import gcp_utils


class AssetStorageManager:
    def __init__(self, config: dict, asset_path: str, encryption_key_file: str):
        self.config = gcp_utils.GCPAssetConfig(**config)

        self.asset_path = asset_path
        self.encryption_key_file = encryption_key_file

    def __create_bucket(self):
        gcp_utils.create_storage_bucket(self.config)

    def __encrypt_asset(self):
        tmp_encrypted_asset_path = generate_tmp_path()
        SymmetricEncryption().encrypt_file(
            self.asset_path, self.encryption_key_file, tmp_encrypted_asset_path
        )
        asset_hash = get_file_hash(tmp_encrypted_asset_path)
        return tmp_encrypted_asset_path, asset_hash

    def __upload_encrypted_asset(self, tmp_encrypted_asset_path):
        gcp_utils.upload_file_to_gcs(
            self.config,
            tmp_encrypted_asset_path,
            f"gs://{self.config.bucket}/{self.config.encrypted_asset_bucket_file}",
        )

    def __grant_bucket_public_read_access(self):
        gcp_utils.add_bucket_iam_policy_binding(
            self.config, "allUsers", "roles/storage.objectViewer"
        )

    def setup(self):
        self.__create_bucket()
        self.__grant_bucket_public_read_access()

    def store_asset(self):
        tmp_encrypted_asset_path, asset_hash = self.__encrypt_asset()
        self.__upload_encrypted_asset(tmp_encrypted_asset_path)
        return asset_hash

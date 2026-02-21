from google.cloud import storage
from .utils import GCPAssetConfig


class GCPStorage:
    def __init__(self, asset_config_dict: dict):
        asset_config = GCPAssetConfig(**asset_config_dict)
        self.bucket_name = asset_config.bucket
        self.asset_path = asset_config.encrypted_asset_bucket_file

        self.storage_client = None

    def initialize(self) -> None:
        self.storage_client = storage.Client()

    def get_asset(self, output_path: str) -> None:
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(self.asset_path)
        blob.download_to_filename(output_path)

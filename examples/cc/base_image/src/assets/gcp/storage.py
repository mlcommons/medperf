from google.cloud import storage

from .utils import GCPStorageConfig, get_credentials


class GCPStorage:
    def __init__(self, storage_config_dict: dict):
        config = GCPStorageConfig(**storage_config_dict)
        self.bucket_name = config.bucket
        self.object_path = config.object_path
        self.pool_provider = config.workload_identity_pool_provider
        self.storage_client = None

    def initialize(self) -> None:
        self.storage_client = storage.Client(
            credentials=get_credentials(self.pool_provider)
        )

    def get_asset(self, output_path: str) -> None:
        bucket = self.storage_client.bucket(self.bucket_name)
        bucket.blob(self.object_path).download_to_filename(output_path)

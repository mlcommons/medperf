from google.cloud import storage
from .utils import GCPResultConfig
from uuid import uuid4


class GCPResult:
    def __init__(self, result_config_dict: dict):
        result_config = GCPResultConfig(**result_config_dict)
        self.bucket_name = result_config.bucket
        self.output_result_path = result_config.encrypted_result_bucket_file
        self.output_key_path = result_config.encrypted_key_bucket_file
        self.storage_client = None

    def initialize(self) -> None:
        self.storage_client = storage.Client()

    def write_result(self, result_path: str) -> None:
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(self.output_result_path)
        blob.upload_from_filename(result_path)

    def write_key(self, key_bytes: bytes) -> None:
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(self.output_key_path)
        blob.upload_from_string(key_bytes)

    def do_test(self, test_data: bytes) -> None:
        bucket = self.storage_client.bucket(self.bucket_name)
        path = f"test_{uuid4().hex}"
        blob = bucket.blob(path)
        blob.upload_from_string(test_data)

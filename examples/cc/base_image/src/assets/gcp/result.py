from uuid import uuid4

from google.cloud import storage

from .utils import GCPResultConfig


class GCPResult:
    def __init__(self, result_config_dict: dict):
        config = GCPResultConfig(**result_config_dict)
        self.bucket_name = config.bucket
        self.output_result_path = config.encrypted_result_bucket_file
        self.output_key_path = config.encrypted_key_bucket_file
        self.storage_client = None

    def initialize(self) -> None:
        self.storage_client = storage.Client()

    def write_result(self, result_path: str) -> None:
        bucket = self.storage_client.bucket(self.bucket_name)
        bucket.blob(self.output_result_path).upload_from_filename(result_path)

    def write_key(self, key_bytes: bytes) -> None:
        bucket = self.storage_client.bucket(self.bucket_name)
        bucket.blob(self.output_key_path).upload_from_string(key_bytes)

    def do_test(self, test_data: bytes) -> None:
        bucket = self.storage_client.bucket(self.bucket_name)
        bucket.blob(f"test_{uuid4().hex}").upload_from_string(test_data)

"""Results left in a Google Cloud Storage bucket the collector owns."""

from pydantic import BaseModel

from medperf_cc.backends.gcp import checks
from medperf_cc.backends.gcp.credentials import get_user_credentials
from medperf_cc.errors import ConfigurationError
from medperf_cc.identity import WorkloadIdentity
from medperf_cc.result_store.base import ResultStore
from medperf_cc.storage.gcp import client as gcs

GCP_RESULT_STORE = "gcp"

OBJECT_ADMIN_ROLE = "roles/storage.objectAdmin"


class GCPResultStoreConfig(BaseModel):
    bucket: str

    class Config:
        extra = "ignore"


class GCPResultStore(ResultStore):
    SETTINGS = GCPResultStoreConfig

    def __init__(self, config: dict):
        super().__init__(config)
        self.gcp = GCPResultStoreConfig(**config)

    @property
    def backend(self) -> str:
        return GCP_RESULT_STORE

    def verify(self) -> None:
        problem = checks.check_user_role_on_bucket(
            "user", get_user_credentials(), self.gcp.bucket, OBJECT_ADMIN_ROLE
        )
        if problem:
            raise ConfigurationError(
                f"Result store setup verification failed: {problem}"
            )

    def store_config(self, workload: WorkloadIdentity) -> dict:
        return {
            "backend": self.backend,
            "bucket": self.gcp.bucket,
            "encrypted_result_bucket_file": workload.results_path,
            "encrypted_key_bucket_file": workload.results_encryption_key_path,
        }

    def results_ready(self, workload: WorkloadIdentity) -> bool:
        if not gcs.file_exists(self.gcp.bucket, workload.results_path):
            return False
        return gcs.file_exists(self.gcp.bucket, workload.results_encryption_key_path)

    def fetch(self, workload: WorkloadIdentity, encrypted_results_path: str) -> bytes:
        gcs.download_file(
            self.gcp.bucket, workload.results_path, encrypted_results_path
        )
        return gcs.download_string(
            self.gcp.bucket, workload.results_encryption_key_path
        )

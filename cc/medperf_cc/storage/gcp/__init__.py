"""An asset's ciphertext in a Google Cloud Storage bucket.

Read access is an IAM binding on the bucket, granted to the principals a
workload identity pool derives from an attestation -- the same principals the
GCP vault grants the key to.
"""

from typing import List

from pydantic import BaseModel

from medperf_cc.backends.gcp import checks
from medperf_cc.backends.gcp.config import WorkloadIdentityPool
from medperf_cc.backends.gcp.credentials import get_user_credentials
from medperf_cc.errors import ConfigurationError
from medperf_cc.storage.base import AssetStorage
from medperf_cc.storage.gcp import client

GCP_STORAGE = "gcp"

OBJECT_VIEWER_ROLE = "roles/storage.objectViewer"
BUCKET_ADMIN_ROLE = "roles/storage.admin"


class GCPStorageConfig(BaseModel):
    bucket: str
    project_number: str
    wip: str
    # The workload federates against the provider, not the pool.
    wip_provider: str

    class Config:
        extra = "ignore"


class GCPStorage(AssetStorage):
    SETTINGS = GCPStorageConfig

    def __init__(self, config: dict, asset_name: str):
        super().__init__(config, asset_name)
        self.gcp = GCPStorageConfig(**config)
        self.pool = WorkloadIdentityPool(**config)

    @property
    def backend(self) -> str:
        return GCP_STORAGE

    @property
    def object_path(self) -> str:
        return f"{self.asset_name}.enc"

    def verify(self) -> None:
        problem = checks.check_user_role_on_bucket(
            "user", get_user_credentials(), self.gcp.bucket, BUCKET_ADMIN_ROLE
        )
        if problem:
            raise ConfigurationError(f"Asset storage is not usable: {problem}")

    def publish(self, encrypted_asset_file) -> None:
        client.upload_file_object(
            self.gcp.bucket, encrypted_asset_file, self.object_path
        )

    def permit(self, identities: List[str]) -> None:
        client.set_iam_policy(
            self.gcp.bucket,
            [self.pool.principal(identity) for identity in identities],
            OBJECT_VIEWER_ROLE,
        )

    def workload_config(self) -> dict:
        return {
            "backend": self.backend,
            "bucket": self.gcp.bucket,
            "object_path": self.object_path,
            "workload_identity_pool_provider": self.pool.provider_name,
        }

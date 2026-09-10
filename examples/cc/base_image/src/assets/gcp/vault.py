from google.cloud import kms, storage

from .utils import GCPVaultConfig, get_credentials


class GCPVault:
    """The wrapped key comes from a bucket; unwrapping it is what needs the
    attestation, since only a permitted workload may use the KMS key."""

    def __init__(self, vault_config_dict: dict):
        config = GCPVaultConfig(**vault_config_dict)
        self.bucket_name = config.bucket
        self.wrapped_key_path = config.wrapped_key_path
        self.key_name = config.key_name
        self.pool_provider = config.workload_identity_pool_provider

        self.kms_client = None
        self.storage_client = None

    def initialize(self) -> None:
        creds = get_credentials(self.pool_provider)
        self.kms_client = kms.KeyManagementServiceClient(credentials=creds)
        self.storage_client = storage.Client(credentials=creds)

    def get_key(self, output_path: str) -> None:
        bucket = self.storage_client.bucket(self.bucket_name)
        wrapped = bucket.blob(self.wrapped_key_path).download_as_bytes()
        response = self.kms_client.decrypt(
            request=kms.DecryptRequest(name=self.key_name, ciphertext=wrapped)
        )
        with open(output_path, "wb") as f:
            f.write(response.plaintext)

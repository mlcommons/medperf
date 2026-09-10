from dataclasses import dataclass
import os

from google.auth import load_credentials_from_dict
from google.auth.credentials import Credentials


def get_credentials(pool_provider: str) -> Credentials:
    """Federates this workload's attestation into Google credentials.

    The launcher writes the attested claims token to a well known path; Google
    exchanges it for a short lived credential matching whatever principal the
    workload identity pool derives from it."""
    if os.getenv("DRY_RUN", None):
        return
    info = {
        "type": "external_account",
        "audience": f"//iam.googleapis.com/{pool_provider}",
        "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
        "token_url": "https://sts.googleapis.com/v1/token",
        "credential_source": {
            "file": "/run/container_launcher/attestation_verifier_claims_token"
        },
    }
    creds, _ = load_credentials_from_dict(info)
    return creds


@dataclass
class GCPStorageConfig:
    backend: str
    bucket: str
    object_path: str
    workload_identity_pool_provider: str


@dataclass
class GCPVaultConfig:
    backend: str
    bucket: str
    wrapped_key_path: str
    key_name: str
    workload_identity_pool_provider: str


@dataclass
class GCPResultConfig:
    backend: str
    bucket: str
    encrypted_result_bucket_file: str
    encrypted_key_bucket_file: str

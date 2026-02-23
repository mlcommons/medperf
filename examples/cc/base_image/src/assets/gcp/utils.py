from dataclasses import dataclass
from google.auth.credentials import Credentials
from google.auth import load_credentials_from_dict
import os


def get_credentials(wippro: str) -> Credentials:
    if os.getenv("DRY_RUN", None):
        return
    info = {
        "type": "external_account",
        "audience": f"//iam.googleapis.com/{wippro}",
        "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
        "token_url": "https://sts.googleapis.com/v1/token",
        "credential_source": {
            "file": "/run/container_launcher/attestation_verifier_claims_token"
        },
    }
    creds, _ = load_credentials_from_dict(info)
    return creds


@dataclass
class GCPAssetConfig:
    project_id: str
    project_number: str
    account: str
    bucket: str
    encrypted_asset_bucket_file: str
    encrypted_key_bucket_file: str
    keyring_name: str
    key_name: str
    wip: str

    @property
    def full_key_name(self) -> str:
        return f"projects/{self.project_id}/locations/global/keyRings/{self.keyring_name}/cryptoKeys/{self.key_name}"

    @property
    def full_wip_name(self) -> str:
        return f"projects/{self.project_number}/locations/global/workloadIdentityPools/{self.wip}/providers/attestation-verifier"


@dataclass
class GCPResultConfig:
    bucket: str
    encrypted_result_bucket_file: str
    encrypted_key_bucket_file: str

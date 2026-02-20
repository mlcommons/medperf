"""Utility functions for GCP operations."""

from medperf.utils import run_command
from dataclasses import dataclass
from google.cloud import kms
from google.iam.v1 import policy_pb2


GCP_EXEC = "gcloud"


@dataclass
class GCPOperatorConfig:
    project_id: str
    service_account_name: str
    account: str
    vm_name: str
    bucket: str

    @property
    def service_account_email(self):
        return f"{self.service_account_name}@{self.project_id}.iam.gserviceaccount.com"


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


# IAM Service Account operations
def create_service_account(service_account_name: str):
    """Create service account for workload."""
    cmd = [
        GCP_EXEC,
        "iam",
        "service-accounts",
        "create",
        service_account_name,
    ]
    run_command(cmd)


def add_service_account_iam_policy_binding(
    service_account_email: str, member: str, role: str
):
    """Add IAM policy binding to service account."""
    cmd = [
        GCP_EXEC,
        "iam",
        "service-accounts",
        "add-iam-policy-binding",
        service_account_email,
        f"--member={member}",
        f"--role={role}",
    ]
    run_command(cmd)


def add_project_iam_policy_binding(project_id: str, member: str, role: str):
    """Add IAM policy binding to project."""
    cmd = [
        GCP_EXEC,
        "projects",
        "add-iam-policy-binding",
        project_id,
        f"--member={member}",
        f"--role={role}",
    ]
    run_command(cmd)


# KMS operations
def create_keyring(keyring_name: str):
    """Create KMS keyring."""
    cmd = [
        GCP_EXEC,
        "kms",
        "keyrings",
        "create",
        keyring_name,
        "--location=global",
    ]
    run_command(cmd)


def create_kms_key(key_name: str, keyring_name: str):
    """Create KMS key."""
    cmd = [
        GCP_EXEC,
        "kms",
        "keys",
        "create",
        key_name,
        "--location=global",
        f"--keyring={keyring_name}",
        "--purpose=encryption",
    ]
    run_command(cmd)


def add_kms_key_iam_policy_binding(key_resource: str, member: str, role: str):
    cmd = [
        GCP_EXEC,
        "kms",
        "keys",
        "add-iam-policy-binding",
        key_resource,
        f"--member={member}",
        f"--role={role}",
    ]
    run_command(cmd)


def set_kms_iam_policy(key_resource: str, members: list[str], role: str):
    client = kms.KeyManagementServiceClient()
    # Get current policy
    policy = client.get_iam_policy(request={"resource": key_resource})

    # remove current decryptor roles
    to_remove = []
    for binding in policy.bindings:
        if binding.role == role:
            to_remove.append(binding)

    for binding in to_remove:
        policy.bindings.remove(binding)

    policy.bindings.append(policy_pb2.Binding(role=role, members=members))
    # Set new policy
    client.set_iam_policy(request={"resource": key_resource, "policy": policy})


def encrypt_with_kms_key(plaintext_file: str, ciphertext_file: str, key_resource: str):
    """Encrypt file using KMS key."""
    cmd = [
        GCP_EXEC,
        "kms",
        "encrypt",
        f"--ciphertext-file={ciphertext_file}",
        f"--plaintext-file={plaintext_file}",
        f"--key={key_resource}",
    ]
    run_command(cmd)


# Workload Identity Pool operations
def create_workload_identity_pool(pool_name: str):
    """Create workload identity pool."""
    cmd = [
        GCP_EXEC,
        "iam",
        "workload-identity-pools",
        "create",
        pool_name,
        "--location=global",
    ]
    run_command(cmd)


def create_workload_identity_pool_oidc_provider(
    pool_name: str, attribute_mapping: str, attribute_condition: str
):
    """Create OIDC provider for workload identity pool."""
    cmd = [
        GCP_EXEC,
        "iam",
        "workload-identity-pools",
        "providers",
        "create-oidc",
        "attestation-verifier",
        "--location=global",
        f"--workload-identity-pool={pool_name}",
        "--issuer-uri=https://confidentialcomputing.googleapis.com/",
        "--allowed-audiences=https://sts.googleapis.com",
        f"--attribute-mapping={attribute_mapping}",
        f"--attribute-condition={attribute_condition}",
    ]
    run_command(cmd)


# Storage operations
def create_storage_bucket(bucket_name: str):
    """Create GCS bucket."""
    cmd = [
        GCP_EXEC,
        "storage",
        "buckets",
        "create",
        f"gs://{bucket_name}",
    ]
    run_command(cmd)


def upload_file_to_gcs(local_file: str, gcs_path: str):
    """Upload file to Google Cloud Storage."""
    cmd = [
        GCP_EXEC,
        "storage",
        "cp",
        local_file,
        gcs_path,
    ]
    run_command(cmd)


def add_bucket_iam_policy_binding(bucket_name: str, member: str, role: str):
    """Add IAM policy binding to GCS bucket."""
    cmd = [
        GCP_EXEC,
        "storage",
        "buckets",
        "add-iam-policy-binding",
        f"gs://{bucket_name}",
        f"--member={member}",
        f"--role={role}",
    ]
    run_command(cmd)


# run
def run_workload(
    vm_name: str,
    service_account_email: str,
    metadata: str,
    zone: str = "us-west1-b",
    confidential_compute_type: str = "SEV",
    min_cpu_platform: str = "AMD Milan",
    image_family: str = "confidential-space-debug",
    maintenance_policy: str = "MIGRATE",
):

    cmd = [
        "gcloud",
        "compute",
        "instances",
        "create",
        vm_name,
        f"--confidential-compute-type={confidential_compute_type}",
        "--shielded-secure-boot",
        "--scopes=cloud-platform",
        f"--zone={zone}",
        f"--maintenance-policy={maintenance_policy}",
        f"--min-cpu-platform={min_cpu_platform}",
        "--image-project=confidential-space-images",
        f"--image-family={image_family}",
        f"--service-account={service_account_email}",
        f"--metadata={metadata}",
    ]

    run_command(cmd)

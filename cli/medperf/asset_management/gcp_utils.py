"""Utility functions for GCP operations."""

import logging
from typing import Union
from medperf.exceptions import ExecutionError
from medperf.utils import run_command
from dataclasses import dataclass
from google.cloud import kms
from google.iam.v1 import policy_pb2
from google.cloud import storage
from google.cloud.exceptions import Conflict


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
        return (
            f"projects/{self.project_id}/locations/global/"
            f"keyRings/{self.keyring_name}/cryptoKeys/{self.key_name}"
        )

    @property
    def full_wip_name(self) -> str:
        return (
            f"projects/{self.project_number}/locations/global/"
            f"workloadIdentityPools/{self.wip}/providers/attestation-verifier"
        )


# IAM Service Account operations
def create_service_account(config: GCPOperatorConfig):
    """Create service account for workload."""
    cmd = [
        GCP_EXEC,
        f"--project={config.project_id}",
        "iam",
        "service-accounts",
        "create",
        config.service_account_name,
    ]
    try:
        run_command(cmd)
    except ExecutionError as e:
        logging.debug(
            f"Service account {config.service_account_name} may already exist. Error: {e}"
        )


def add_service_account_iam_policy_binding(
    config: GCPOperatorConfig, member: str, role: str
):
    """Add IAM policy binding to service account."""
    cmd = [
        GCP_EXEC,
        f"--project={config.project_id}",
        "iam",
        "service-accounts",
        "add-iam-policy-binding",
        config.service_account_email,
        f"--member={member}",
        f"--role={role}",
    ]
    run_command(cmd)


def add_project_iam_policy_binding(config: GCPOperatorConfig, member: str, role: str):
    """Add IAM policy binding to project."""
    cmd = [
        GCP_EXEC,
        f"--project={config.project_id}",
        "projects",
        "add-iam-policy-binding",
        config.project_id,
        f"--member={member}",
        f"--role={role}",
    ]
    run_command(cmd)


# KMS operations
def create_keyring(config: GCPAssetConfig):
    """Create KMS keyring."""
    cmd = [
        GCP_EXEC,
        f"--project={config.project_id}",
        "kms",
        "keyrings",
        "create",
        config.keyring_name,
        "--location=global",
    ]
    try:
        run_command(cmd)
    except ExecutionError as e:
        logging.debug(f"Keyring {config.keyring_name} may already exist. Error: {e}")


def create_kms_key(config: GCPAssetConfig):
    """Create KMS key."""
    cmd = [
        GCP_EXEC,
        f"--project={config.project_id}",
        "kms",
        "keys",
        "create",
        config.key_name,
        "--location=global",
        f"--keyring={config.keyring_name}",
        "--purpose=encryption",
    ]
    try:
        run_command(cmd)
    except ExecutionError as e:
        logging.debug(
            f"Key {config.key_name} may already exist in keyring {config.keyring_name}. Error: {e}"
        )


def add_kms_key_iam_policy_binding(config: GCPAssetConfig, member: str, role: str):
    cmd = [
        GCP_EXEC,
        f"--project={config.project_id}",
        "kms",
        "keys",
        "add-iam-policy-binding",
        config.full_key_name,
        f"--member={member}",
        f"--role={role}",
    ]
    run_command(cmd)


def set_kms_iam_policy(config: GCPAssetConfig, members: list[str], role: str):
    client = kms.KeyManagementServiceClient()
    # Get current policy
    policy = client.get_iam_policy(request={"resource": config.full_key_name})

    # remove current decryptor roles
    to_remove = []
    for binding in policy.bindings:
        if binding.role == role:
            to_remove.append(binding)

    for binding in to_remove:
        policy.bindings.remove(binding)

    policy.bindings.append(policy_pb2.Binding(role=role, members=members))
    # Set new policy
    client.set_iam_policy(request={"resource": config.full_key_name, "policy": policy})


def encrypt_with_kms_key(
    config: GCPAssetConfig, plaintext_file: str, ciphertext_file: str
):
    """Encrypt file using KMS key."""
    cmd = [
        GCP_EXEC,
        f"--project={config.project_id}",
        "kms",
        "encrypt",
        f"--ciphertext-file={ciphertext_file}",
        f"--plaintext-file={plaintext_file}",
        f"--key={config.full_key_name}",
    ]
    run_command(cmd)


# Workload Identity Pool operations
def create_workload_identity_pool(config: GCPAssetConfig):
    """Create workload identity pool."""
    cmd = [
        GCP_EXEC,
        f"--project={config.project_id}",
        "iam",
        "workload-identity-pools",
        "create",
        config.wip,
        "--location=global",
    ]
    try:
        run_command(cmd)
    except ExecutionError as e:
        logging.debug(
            f"Workload identity pool {config.wip} may already exist. Error: {e}"
        )


def create_workload_identity_pool_oidc_provider(
    config: GCPAssetConfig, attribute_mapping: str, attribute_condition: str
):
    """Create OIDC provider for workload identity pool."""
    cmd = [
        GCP_EXEC,
        f"--project={config.project_id}",
        "iam",
        "workload-identity-pools",
        "providers",
        "create-oidc",
        "attestation-verifier",
        "--location=global",
        f"--workload-identity-pool={config.wip}",
        "--issuer-uri=https://confidentialcomputing.googleapis.com/",
        "--allowed-audiences=https://sts.googleapis.com",
        f"--attribute-mapping={attribute_mapping}",
        f"--attribute-condition={attribute_condition}",
    ]
    try:
        run_command(cmd)
        return
    except ExecutionError as e:
        logging.debug(
            f"OIDC provider for workload identity pool {config.wip} may already exist. Error: {e}"
        )
    # try updating the provider if it already exists
    cmd = [
        GCP_EXEC,
        f"--project={config.project_id}",
        "iam",
        "workload-identity-pools",
        "providers",
        "update-oidc",
        "attestation-verifier",
        "--location=global",
        f"--workload-identity-pool={config.wip}",
        f"--attribute-mapping={attribute_mapping}",
        f"--attribute-condition={attribute_condition}",
    ]
    run_command(cmd)
    logging.debug(
        f"Updated OIDC provider for workload identity pool {config.wip}"
        f" with new attribute mapping and condition."
    )


# Storage operations
def create_storage_bucket(config: Union[GCPAssetConfig, GCPOperatorConfig]):
    """Create GCS bucket."""
    client = storage.Client(project=config.project_id)
    for bucket in client.list_buckets(project=config.project_id):
        if bucket.name == config.bucket:
            logging.debug(f"Bucket {config.bucket} already exists.")
            return

    # try creating the bucket
    try:
        client.create_bucket(config.bucket, project=config.project_id)
    except Conflict as e:
        logging.debug(f"Bucket {config.bucket} already exists. Conflict: {e}")


def upload_file_to_gcs(
    config: Union[GCPAssetConfig, GCPOperatorConfig], local_file: str, gcs_path: str
):
    """Upload file to Google Cloud Storage."""
    cmd = [
        GCP_EXEC,
        f"--project={config.project_id}",
        "storage",
        "cp",
        local_file,
        gcs_path,
    ]
    run_command(cmd)


def add_bucket_iam_policy_binding(
    config: Union[GCPAssetConfig, GCPOperatorConfig], member: str, role: str
):
    """Add IAM policy binding to GCS bucket."""
    cmd = [
        GCP_EXEC,
        f"--project={config.project_id}",
        "storage",
        "buckets",
        "add-iam-policy-binding",
        f"gs://{config.bucket}",
        f"--member={member}",
        f"--role={role}",
    ]
    run_command(cmd)


# run
def run_workload(
    config: GCPOperatorConfig,
    metadata: str,
    zone: str = "us-west1-b",
    confidential_compute_type: str = "SEV",
    min_cpu_platform: str = "AMD Milan",
    image_family: str = "confidential-space-debug",
    maintenance_policy: str = "MIGRATE",
):

    cmd = [
        "gcloud",
        f"--project={config.project_id}",
        "compute",
        "instances",
        "create",
        config.vm_name,
        f"--confidential-compute-type={confidential_compute_type}",
        "--shielded-secure-boot",
        "--scopes=cloud-platform",
        f"--zone={zone}",
        f"--maintenance-policy={maintenance_policy}",
        f"--min-cpu-platform={min_cpu_platform}",
        "--image-project=confidential-space-images",
        f"--image-family={image_family}",
        f"--service-account={config.service_account_email}",
        f"--metadata={metadata}",
    ]

    run_command(cmd)

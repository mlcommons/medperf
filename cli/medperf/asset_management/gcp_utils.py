"""Utility functions for GCP operations."""

from medperf.utils import run_command

POLICY_ATTRIBUTES_MAPPING = {
    "image_digest": "assertion.submods.container.image_digest",
}

GCP_EXEC = "gcloud"


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
    """Add IAM policy binding to KMS key."""
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


def create_workload_identity_pool_oidc_provider(pool_name: str, attribute_mapping: str):
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
        '--attribute-condition=assertion.swname == "CONFIDENTIAL_SPACE"',
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

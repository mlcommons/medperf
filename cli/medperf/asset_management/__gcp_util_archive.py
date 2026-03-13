import logging
from typing import Union
from medperf.exceptions import ExecutionError
from medperf.utils import run_command

from google.cloud import storage
from google.cloud.exceptions import Conflict

from .gcp_utils import GCPOperatorConfig, GCPAssetConfig, CCWorkloadID

GCP_EXEC = "gcloud"


# IAM Service Account operations
def create_service_account(config: GCPOperatorConfig):
    """Create service account for workload."""
    cmd = [
        GCP_EXEC,
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
        "kms",
        "keyrings",
        "create",
        config.keyring_name,
        f"--location={config.key_location}",
    ]
    try:
        run_command(cmd)
    except ExecutionError as e:
        logging.debug(f"Keyring {config.keyring_name} may already exist. Error: {e}")


def create_kms_key(config: GCPAssetConfig):
    """Create KMS key."""
    cmd = [
        GCP_EXEC,
        "kms",
        "keys",
        "create",
        config.key_name,
        f"--location={config.key_location}",
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
        "kms",
        "keys",
        "add-iam-policy-binding",
        config.full_key_name,
        f"--member={member}",
        f"--role={role}",
    ]
    run_command(cmd)


# Workload Identity Pool operations
def create_workload_identity_pool(config: GCPAssetConfig):
    """Create workload identity pool."""
    cmd = [
        GCP_EXEC,
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
        "iam",
        "workload-identity-pools",
        "providers",
        "create-oidc",
        config.wip_provider,
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


def add_bucket_iam_policy_binding(
    config: Union[GCPAssetConfig, GCPOperatorConfig], member: str, role: str
):
    """Add IAM policy binding to GCS bucket."""
    cmd = [
        GCP_EXEC,
        "storage",
        "buckets",
        "add-iam-policy-binding",
        f"gs://{config.bucket}",
        f"--member={member}",
        f"--role={role}",
    ]
    run_command(cmd)


# vm creation
# run
def run_workload(
    config: GCPOperatorConfig, workload_config: CCWorkloadID, metadata: dict[str, str]
):
    metadata = "^~^" + "~".join([f"{key}={value}" for key, value in metadata.items()])
    # note: machine type and cc type must conform somehow
    cmd = [
        GCP_EXEC,
        "compute",
        "instances",
        "create",
        workload_config.vm_name,
        f"--confidential-compute-type={config.cc_type}",
        "--shielded-secure-boot",
        "--scopes=cloud-platform",
        f"--boot-disk-size={config.boot_disk_size}G",
        f"--zone={config.vm_zone}",
        f"--network={config.vm_network}",
        "--maintenance-policy=MIGRATE",
        f"--min-cpu-platform={config.min_cpu_platform}",
        "--image-project=confidential-space-images",
        "--image-family=confidential-space",
        f"--machine-type={config.machine_type}",
        f"--service-account={config.service_account_email}",
        f"--metadata={metadata}",
    ]

    run_command(cmd)


def run_gpu_workload(
    config: GCPOperatorConfig, workload_config: CCWorkloadID, metadata: dict[str, str]
):
    # note: --image-family=confidential-space-preview-cgpu
    # note: boot disk size must be at least 30GB
    metadata = "^~^" + "~".join([f"{key}={value}" for key, value in metadata.items()])
    cmd = [
        GCP_EXEC,
        "beta",
        "compute",
        "instance-templates",
        "create",
        workload_config.vm_template_name,
        "--provisioning-model=FLEX_START",
        "--confidential-compute-type=TDX",
        "--machine-type=a3-highgpu-1g",
        "--maintenance-policy=TERMINATE",
        "--shielded-secure-boot",
        "--image-project=confidential-space-images",
        "--image-family=confidential-space-debug-preview-cgpu",
        f"--service-account={config.service_account_email}",
        "--scopes=cloud-platform",
        f"--boot-disk-size={config.boot_disk_size}G",
        "--reservation-affinity=none",
        f"--max-run-duration={config.run_duration}h",
        "--instance-termination-action=DELETE",
        f"--metadata={metadata}",
    ]

    run_command(cmd)

    if config.vm_zone not in ["us-central1-a", "europe-west4-c", "us-east5-a"]:
        raise ValueError(
            "GPU workloads can only be run in us-central1-a, europe-west4-c, or us-east5-a zones."
        )

    cmd = [
        GCP_EXEC,
        "compute",
        "instance-groups",
        "managed",
        "create",
        workload_config.instance_group_name,
        f"--template={workload_config.vm_template_name}",
        f"--zone={config.vm_zone}",
        "--size=0",
        "--default-action-on-vm-failure=do_nothing",
    ]
    run_command(cmd)

    cmd = [
        GCP_EXEC,
        "compute",
        "instance-groups",
        "managed",
        "resize-requests",
        "create",
        workload_config.instance_group_name,
        f"--resize-request={workload_config.resize_request_name}",
        "--resize-by=1",
        f"--zone={config.vm_zone}",
    ]
    run_command(cmd)


"""
from google.auth import impersonated_credentials

### checks

def impersonate_service_account(base_creds, sa_email):
    logging.debug(f"Impersonating service account: {sa_email}")
    try:
        return impersonated_credentials.Credentials(
            source_credentials=base_creds,
            target_principal=sa_email,
            target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
    except Exception as e:
        logging.debug(f"Failed to impersonate service account {sa_email}: {e}")
        return None


# ---------------------------------------------------------------------------
# Service Account roles
# ---------------------------------------------------------------------------


def check_sa_roles_for_project(sa_creds, project_id, role):

    logging.debug(f"Checking service account project permissions: {project_id}")
    try:
        permissions = get_role_permissions(
            role, "//cloudresourcemanager.googleapis.com/projects/_"
        )
        crm = googleapiclient.discovery.build(
            "cloudresourcemanager", "v1", credentials=sa_creds, cache_discovery=False
        )
        granted = (
            crm.projects()
            .testIamPermissions(resource=project_id, body={"permissions": permissions})
            .execute()
        )
        granted_permissions = granted.get("permissions", [])
        missing = set(permissions) - set(granted_permissions)
        if missing:
            logging.debug(f"Missing permissions: {missing}")
            return (
                f"(Role {role}) Service account missing permissions: "
                f"{missing} on project: {project_id}"
            )
        return None
    except Exception as e:
        logging.debug(f"check_sa_project_permissions exception: {e}")
        return f"Failed to verify service account role on project: {project_id}"



def check_user_role_on_vm(creds, project_id, vm_name, vm_zone, role):

    logging.debug(f"Checking if user has {role} role on VM: {vm_name}")
    try:
        permissions = get_role_permissions(
            role,
            "//compute.googleapis.com/projects/_/zones/_/instances/_",
        )
        compute = googleapiclient.discovery.build(
            "compute", "v1", credentials=creds, cache_discovery=False
        )
        granted = (
            compute.instances()
            .testIamPermissions(
                project=project_id,
                zone=vm_zone,
                resource=vm_name,
                body={"permissions": permissions},
            )
            .execute()
        )
        granted_permissions = granted.get("permissions", [])
        missing = set(permissions) - set(granted_permissions)
        if missing:
            logging.debug(f"Missing permissions: {missing}")
            return f"(Role {role}) user missing permissions: {missing} on VM: {vm_name}"
        return None
    except Exception as e:
        logging.debug(f"check_user_role_on_vm exception: {e}")
        return f"Failed to verify user role on VM: {vm_name}"

"""

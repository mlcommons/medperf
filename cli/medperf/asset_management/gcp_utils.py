"""Utility functions for GCP operations."""

import logging
from typing import Union
from medperf.utils import run_command
from google.cloud import kms
from google.iam.v1 import policy_pb2
from google.cloud import compute_v1, storage
import time
from colorama import Fore, Style
import medperf.config as medperf_config
from pydantic import BaseModel

GCP_EXEC = "gcloud"


# TODO: validation of inputs
class CCWorkloadID(BaseModel):
    data_hash: str
    model_hash: str
    script_hash: str
    result_collector_hash: str
    data_id: int
    model_id: int
    script_id: int
    execution_id: int = None

    @property
    def id(self):
        return "::".join(
            [
                self.script_hash,
                self.data_hash,
                self.model_hash,
                self.result_collector_hash,
            ]
        )

    @property
    def id_for_model(self):
        return "::".join(
            [
                self.script_hash,
                self.model_hash,
            ]
        )

    @property
    def human_readable_id(self):
        if self.execution_id:
            return f"d{self.data_id}-m{self.model_id}-s{self.script_id}-e{self.execution_id}"
        return f"d{self.data_id}-m{self.model_id}-s{self.script_id}"

    @property
    def vm_template_name(self):
        return f"{self.human_readable_id}-vm-template"

    @property
    def instance_group_name(self):
        return f"{self.human_readable_id}-vm-instance-group"

    @property
    def resize_request_name(self):
        return f"{self.human_readable_id}-vm-instance-group-resize-request"

    @property
    def vm_name(self):
        # not used
        return f"{self.human_readable_id}-cvm"

    @property
    def results_path(self):
        return f"{self.human_readable_id}/output"

    @property
    def results_encryption_key_path(self):
        return f"{self.human_readable_id}/encryption_key"


class GCPOperatorConfig(BaseModel):
    project_id: str
    service_account_name: str
    bucket: str
    machine_type: str
    boot_disk_size: int  # GB
    vm_name: str = "testcc"
    vm_zone: str
    vm_network: str
    logs_poll_frequency: int = 30  # seconds
    gpu: bool
    run_duration: int = 24  # hours, only applicable for GPU workloads

    @property
    def min_cpu_platform(self):
        # TODO: check
        return "AMD Milan"

    @property
    def cc_type(self):
        # TODO: check
        return "SEV"

    @property
    def service_account_email(self):
        return f"{self.service_account_name}@{self.project_id}.iam.gserviceaccount.com"


class GCPAssetConfig(BaseModel):
    project_id: str
    project_number: str
    bucket: str
    encrypted_asset_bucket_file: str
    encrypted_key_bucket_file: str
    keyring_name: str
    key_name: str
    key_location: str
    wip: str
    wip_provider: str

    @property
    def full_key_name(self) -> str:
        return (
            f"projects/{self.project_id}/locations/{self.key_location}/"
            f"keyRings/{self.keyring_name}/cryptoKeys/{self.key_name}"
        )

    @property
    def full_wip_provider_name(self) -> str:
        return (
            f"projects/{self.project_number}/locations/global/"
            f"workloadIdentityPools/{self.wip}/providers/{self.wip_provider}"
        )

    @property
    def full_wip_name(self) -> str:
        return (
            f"projects/{self.project_number}/locations/global/"
            f"workloadIdentityPools/{self.wip}"
        )


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
        "kms",
        "encrypt",
        f"--ciphertext-file={ciphertext_file}",
        f"--plaintext-file={plaintext_file}",
        f"--key={config.full_key_name}",
    ]
    run_command(cmd)


def update_workload_identity_pool_oidc_provider(
    config: GCPAssetConfig, attribute_mapping: str, attribute_condition: str
):
    cmd = [
        GCP_EXEC,
        "iam",
        "workload-identity-pools",
        "providers",
        "update-oidc",
        config.wip_provider,
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


def upload_file_to_gcs(
    config: Union[GCPAssetConfig, GCPOperatorConfig], local_file: str, gcs_path: str
):
    """Upload file to Google Cloud Storage."""
    cmd = [
        GCP_EXEC,
        "storage",
        "cp",
        local_file,
        gcs_path,
    ]
    run_command(cmd)


def download_file_from_gcs(
    config: Union[GCPAssetConfig, GCPOperatorConfig], gcs_path: str, local_file: str
):
    """Download file from Google Cloud Storage."""
    cmd = [
        GCP_EXEC,
        "storage",
        "cp",
        gcs_path,
        local_file,
    ]
    run_command(cmd)


def check_gcs_file_exists(
    config: Union[GCPAssetConfig, GCPOperatorConfig], gcs_path: str
) -> bool:
    client = storage.Client()
    bucket = client.bucket(config.bucket)
    return bucket.blob(gcs_path).exists()


def set_gcs_iam_policy(config: GCPAssetConfig, members: list[str], role: str):
    client = storage.Client()
    # Get current policy

    policy = client.bucket(config.bucket).get_iam_policy()

    # remove current objectviewer roles
    to_remove = []
    for binding in policy.bindings:
        if binding["role"] == role:
            to_remove.append(binding)

    for binding in to_remove:
        policy.bindings.remove(binding)

    policy.bindings.append({"role": role, "members": members})

    # Set new policy
    client.bucket(config.bucket).set_iam_policy(policy)


def run_workload(config: GCPOperatorConfig, metadata: dict[str, str]):
    """Run workload on GCP."""
    client = compute_v1.InstancesClient()
    project_id = config.project_id
    zone = config.vm_zone
    instance_name = config.vm_name

    instance = client.get(project=project_id, zone=zone, instance=instance_name)
    metadata_items = []
    for key, value in metadata.items():
        metadata_items.append(compute_v1.Items(key=key, value=value))

    metadata_resource = compute_v1.Metadata(
        fingerprint=instance.metadata.fingerprint,
        items=metadata_items,
    )

    client.set_metadata(
        project=project_id,
        zone=zone,
        instance=instance_name,
        metadata_resource=metadata_resource,
    )

    client.start(project=project_id, zone=zone, instance=instance_name)


def wait_for_workload_completion(
    config: GCPOperatorConfig, workload_config: CCWorkloadID
):

    client = compute_v1.InstancesClient()
    project_id = config.project_id
    zone = config.vm_zone
    instance_name = workload_config.vm_name
    next_start = 0
    while True:
        instance = client.get(project=project_id, zone=zone, instance=instance_name)
        status = instance.status
        if status == "TERMINATED":
            return "TERMINATED"
        request = compute_v1.GetSerialPortOutputInstanceRequest(
            project=project_id,
            zone=zone,
            instance=instance_name,
            start=next_start,
        )
        output = client.get_serial_port_output(request=request)
        if output.contents:
            next_start = output.next_
            medperf_config.ui.print_subprocess_logs(
                f"{Fore.WHITE}{Style.DIM}{output.contents}{Style.RESET_ALL}"
            )
            logging.debug(output.contents)

        time.sleep(config.logs_poll_frequency)

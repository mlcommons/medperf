from pydantic import BaseModel


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
    vm_name: str = "gputest"
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

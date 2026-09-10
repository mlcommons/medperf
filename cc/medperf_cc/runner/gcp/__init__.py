"""Running a workload on a Google Confidential Space VM.

The machine and nothing else. Where the results land is the collector's, and
they may not be the operator -- see `medperf_cc.result_store`.
"""

from typing import Iterator

from pydantic import BaseModel

from medperf_cc.backends.gcp import checks
from medperf_cc.backends.gcp.credentials import get_user_credentials
from medperf_cc.errors import ConfigurationError, OperationError
from medperf_cc.identity import WorkloadIdentity
from medperf_cc.runner.base import WorkloadRunner
from medperf_cc.runner.gcp.compute import run_workload, wait_for_workload_completion

GCP_RUNNER = "gcp"

SERVICE_ACCOUNT_USER_ROLE = "roles/iam.serviceAccountUser"


class GCPRunnerConfig(BaseModel):
    project_id: str
    service_account_name: str
    vm_name: str
    vm_zone: str
    logs_poll_frequency: int = 30  # seconds

    @property
    def service_account_email(self) -> str:
        return f"{self.service_account_name}@{self.project_id}.iam.gserviceaccount.com"

    class Config:
        extra = "ignore"


class ConfidentialSpaceRunner(WorkloadRunner):
    SETTINGS = GCPRunnerConfig

    def __init__(self, config: dict):
        super().__init__(config)
        self.gcp = GCPRunnerConfig(**config)

    @property
    def backend(self) -> str:
        return GCP_RUNNER

    def verify(self) -> None:
        credentials = get_user_credentials()
        problem = checks.check_user_role_on_service_account(
            credentials, self.gcp.service_account_email, SERVICE_ACCOUNT_USER_ROLE
        )
        if problem:
            raise ConfigurationError(f"Operator setup verification failed: {problem}")

    def launch(self, workload: WorkloadIdentity, image: str, env: dict) -> None:
        metadata = {
            "tee-image-reference": image,
            "tee-container-log-redirect": "true",
        }
        for key, value in env.items():
            metadata[f"tee-env-{key}"] = value

        try:
            run_workload(self.gcp, metadata)
        except Exception:
            raise OperationError(
                "Failed to run workload: User lacks permissions or VM does not exist"
            )

    def wait(self, workload: WorkloadIdentity) -> Iterator[str]:
        return wait_for_workload_completion(self.gcp, workload)

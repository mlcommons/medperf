"""Starting a confidential workload and watching it run.

Transport only, and only the launching half: where the output goes belongs to
whoever the results are for, which need not be the operator, so it arrives here
as something the caller worked out rather than something this decides. See
`medperf_cc.result_store`.
"""

from abc import ABC, abstractmethod
from typing import Iterator

from medperf_cc.identity import WorkloadIdentity
from medperf_cc.workload import workload_env


class WorkloadRunner(ABC):
    def __init__(self, config: dict):
        self.config = config

    def start(
        self,
        workload: WorkloadIdentity,
        image: str,
        data_config: dict,
        model_config: dict,
        result_config: dict,
        result_collector_public_key: str,
    ) -> None:
        """Starts a workload, told where to fetch its inputs and leave its
        output.

        All four come from elsewhere: the assets from their owners, the
        destination and the key from the collector. The operator supplies the
        machine and nothing about what runs on it."""
        self.launch(
            workload,
            image,
            workload_env(
                workload,
                data_config,
                model_config,
                result_config,
                result_collector_public_key,
            ),
        )

    @property
    @abstractmethod
    def backend(self) -> str:
        """The name a configuration uses to select this runner."""

    @abstractmethod
    def verify(self) -> None:
        """Fails unless this user can operate workloads here."""

    @abstractmethod
    def launch(self, workload: WorkloadIdentity, image: str, env: dict) -> None:
        """Runs the workload's container image with `env` in its environment."""

    @abstractmethod
    def wait(self, workload: WorkloadIdentity) -> Iterator[str]:
        """Yields the workload's log output until it stops."""

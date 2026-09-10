"""Where a confidential workload's results are left, and who picks them up.

The collector's own storage, never the operator's. Results are encrypted for
the collector's key, so nobody else could open them wherever they landed -- but
putting them anywhere else would also mean the collector depending on somebody
else to keep them, and asking that somebody to hold ciphertext they can never
read. The destination belongs to the party the results are for.

Two sides use this, and they are not always the same person. Only one of them
holds credentials:

- the operator, before starting a workload, to tell it where to write. That
  needs the address and nothing else, which is why `store_config` is offered
  as a plain function in this package's `__init__`: no credentials, no network,
  nothing for the operator to hold on to.
- the collector, afterwards, to fetch what was written. That needs credentials
  for the storage, which are ambient on their machine and never travel.

Both sides build from the same published settings -- what separates them is
whose machine is running and therefore whose credentials are to hand. There is
no split in the data, so there is none in the type either.
"""

from abc import ABC, abstractmethod

from medperf_cc.identity import WorkloadIdentity


class ResultStore(ABC):
    def __init__(self, config: dict):
        self.config = config

    @property
    @abstractmethod
    def backend(self) -> str:
        """The name a configuration uses to select this result store."""

    @abstractmethod
    def verify(self) -> None:
        """Fails unless the collector can receive results here."""

    @abstractmethod
    def store_config(self, workload: WorkloadIdentity) -> dict:
        """Where the workload is to write, in this backend's shape.

        Travels to the VM as metadata the operator can read, so it carries an
        address and nothing else."""

    @abstractmethod
    def results_ready(self, workload: WorkloadIdentity) -> bool:
        """Whether the workload's output is there to be fetched."""

    @abstractmethod
    def fetch(self, workload: WorkloadIdentity, encrypted_results_path: str) -> bytes:
        """Downloads the encrypted results, and returns their encrypted key."""

"""Results left in a directory on this machine.

Built on the same `MockStore` primitive every other mock backend uses, under
the same root -- which is what lets an operator and a collector who are
different people still find each other without a cloud account between them.
"""

import os

from medperf_cc.backends.mock import MOCK, MockConfig, MockStore
from medperf_cc.identity import WorkloadIdentity
from medperf_cc.result_store.base import ResultStore

RESULTS_FILE = "results.enc"
RESULTS_KEY_FILE = "results_key.enc"


class MockResultStore(ResultStore):
    SETTINGS = MockConfig

    def __init__(self, config: dict):
        super().__init__(config)
        self.mock = MockConfig(**config)

    @property
    def backend(self) -> str:
        return MOCK

    def verify(self) -> None:
        os.makedirs(self.mock.root, exist_ok=True)

    def store_config(self, workload: WorkloadIdentity) -> dict:
        return {
            "backend": self.backend,
            "root": self.mock.root,
            "results_name": workload.storage_prefix,
        }

    def results_ready(self, workload: WorkloadIdentity) -> bool:
        store = self.__results(workload)
        return store.exists(RESULTS_FILE) and store.exists(RESULTS_KEY_FILE)

    def fetch(self, workload: WorkloadIdentity, encrypted_results_path: str) -> bytes:
        store = self.__results(workload)
        with open(encrypted_results_path, "wb") as f:
            f.write(store.read(RESULTS_FILE))
        return store.read(RESULTS_KEY_FILE)

    def __results(self, workload: WorkloadIdentity) -> MockStore:
        return MockStore({"root": self.mock.root}, workload.storage_prefix)

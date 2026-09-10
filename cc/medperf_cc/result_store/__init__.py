"""Where a workload's results are left, and who picks them up."""

from medperf_cc.backends import backend_of, describe, settings_of
from medperf_cc.backends.mock import MOCK
from medperf_cc.identity import WorkloadIdentity
from medperf_cc.result_store.base import ResultStore
from medperf_cc.result_store.gcp import GCP_RESULT_STORE, GCPResultStore
from medperf_cc.result_store.mock import MockResultStore

RESULT_STORES = {
    GCP_RESULT_STORE: GCPResultStore,
    MOCK: MockResultStore,
}


def result_store_backends() -> dict:
    """Where a collector may choose to receive results, and what each choice
    needs from them."""
    return describe(RESULT_STORES)


def get_result_store(config: dict) -> ResultStore:
    """The store itself, for the collector who holds credentials for it."""
    backend = backend_of(config, RESULT_STORES, "result store")
    return RESULT_STORES[backend](settings_of(config))


def store_config(config: dict, workload: WorkloadIdentity) -> dict:
    """Where a workload is to write, worked out from the collector's settings.

    The whole of what an operator needs from a store they do not own, and the
    whole of what travels to the VM: an address. Nothing here touches the
    network or a credential, which is why the operator is handed a dict rather
    than a store to keep.
    """
    return get_result_store(config).store_config(workload)


__all__ = [
    "RESULT_STORES",
    "ResultStore",
    "get_result_store",
    "store_config",
    "result_store_backends",
]

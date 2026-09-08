"""Where an asset's ciphertext lives, and who may read it."""

from medperf_cc.backends import backend_of, settings_of
from medperf_cc.storage.base import AssetStorage
from medperf_cc.storage.gcp import GCP_STORAGE, GCPStorage
from medperf_cc.storage.mock import MockStorage
from medperf_cc.backends.mock import MOCK

STORAGES = {
    GCP_STORAGE: GCPStorage,
    MOCK: MockStorage,
}


def get_storage(config: dict, asset_name: str) -> AssetStorage:
    backend = backend_of(config, STORAGES, "storage")
    return STORAGES[backend](settings_of(config), asset_name)


__all__ = ["STORAGES", "AssetStorage", "get_storage"]

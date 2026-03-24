from .gcp.result import GCPResult
from .gcp.storage import GCPStorage
from .gcp.key import GCPKey


def storage_manager(asset_config: dict) -> GCPStorage:
    return GCPStorage(asset_config)


def key_manager(asset_config: dict) -> GCPKey:
    return GCPKey(asset_config)


def result_manager(result_config: dict) -> GCPResult:
    return GCPResult(result_config)

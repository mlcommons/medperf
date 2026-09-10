"""An asset's ciphertext in a directory on this machine."""

from typing import List

from medperf_cc.backends.mock import MOCK, MockConfig, MockStore
from medperf_cc.storage.base import AssetStorage

ASSET_FILE = "asset.enc"


class MockStorage(AssetStorage):
    SETTINGS = MockConfig

    def __init__(self, config: dict, asset_name: str):
        super().__init__(config, asset_name)
        self.store = MockStore(config, asset_name)

    @property
    def backend(self) -> str:
        return MOCK

    def verify(self) -> None:
        """Nothing to check: a directory this process can write to is the whole
        of the environment."""

    def publish(self, encrypted_asset_file) -> None:
        self.store.write_stream(ASSET_FILE, encrypted_asset_file)

    def permit(self, identities: List[str]) -> None:
        self.store.set_permitted(identities)

    def workload_config(self) -> dict:
        return {
            "backend": self.backend,
            "root": self.store.config.root,
            "asset_name": self.asset_name,
        }

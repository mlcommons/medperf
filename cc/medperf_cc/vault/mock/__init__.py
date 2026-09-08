"""An asset's key in a directory on this machine.

Kept in a file of its own beside the ciphertext. The workload is asked to name
the identity it is running as, and refused if that is not one of the permitted
ones -- but it is asked, not measured. A real vault reads the same identity out
of an attestation the workload cannot forge, which is the whole difference.
"""

from typing import List

from medperf_cc.backends.mock import MOCK, MockConfig, MockStore
from medperf_cc.identity import WorkloadScope
from medperf_cc.policy import AssetPolicy
from medperf_cc.vault.base import AssetVault

KEY_FILE = "key.bin"


class MockVault(AssetVault):
    SETTINGS = MockConfig

    def __init__(
        self,
        config: dict,
        asset_name: str,
        scope: WorkloadScope,
        policy: AssetPolicy,
    ):
        super().__init__(config, asset_name, scope, policy)
        self.store = MockStore(config, f"{asset_name}_vault")

    @property
    def backend(self) -> str:
        return MOCK

    def verify(self) -> None:
        """Nothing to check: a directory this process can write to is the whole
        of the environment."""

    def publish_key(self, encryption_key: bytes) -> None:
        self.store.write(KEY_FILE, encryption_key)

    def permit(self, identities: List[str]) -> None:
        self.store.set_permitted(identities)

    def workload_config(self) -> dict:
        return {
            "backend": self.backend,
            "root": self.store.config.root,
            "asset_name": self.store.name,
            # Which terms the permitted identities are written over, so the
            # workload can project its own the same way.
            "terms": self.scope.terms,
        }

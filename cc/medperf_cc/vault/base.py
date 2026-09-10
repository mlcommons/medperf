"""Who may have the key that opens an asset.

A vault holds the key and enforces which workload identities may ask for it. It
never encrypts anything: it is handed a key that already exists, because that
key is the asset owner's.
"""

from abc import ABC, abstractmethod
from typing import List

from medperf_cc.identity import WorkloadScope
from medperf_cc.policy import AssetPolicy


class AssetVault(ABC):
    def __init__(
        self,
        config: dict,
        asset_name: str,
        scope: WorkloadScope,
        policy: AssetPolicy,
    ):
        self.config = config
        self.asset_name = asset_name
        # Which terms of a workload's identity this owner pins, and where a
        # workload must run. Both have to reach whatever enforces them.
        self.scope = scope
        self.policy = policy

    @property
    @abstractmethod
    def backend(self) -> str:
        """The name a configuration uses to select this vault."""

    @abstractmethod
    def verify(self) -> None:
        """Fails unless the owner can administer this vault."""

    @abstractmethod
    def publish_key(self, encryption_key: bytes) -> None:
        """Stores the key, and everything a workload must satisfy to get it."""

    @abstractmethod
    def permit(self, identities: List[str]) -> None:
        """Replaces the workload identities allowed to have the key."""

    @abstractmethod
    def workload_config(self) -> dict:
        """What the workload is told, so it can ask for the key.

        Travels to the confidential VM as environment the operator can read, so
        it must carry no secrets."""

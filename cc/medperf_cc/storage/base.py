"""Where an asset's ciphertext lives.

Transport only. The asset arrives already encrypted, because the key belongs to
its owner, and leaves the same way. What a storage backend does decide is who
may read the bytes -- which for some providers is the same grant that releases
the key, and for others is not.
"""

from abc import ABC, abstractmethod
from typing import List


class AssetStorage(ABC):
    def __init__(self, config: dict, asset_name: str):
        self.config = config
        # Derived rather than asked for, so two assets of the same owner cannot
        # collide wherever this backend puts them.
        self.asset_name = asset_name

    @property
    @abstractmethod
    def backend(self) -> str:
        """The name a configuration uses to select this storage."""

    @abstractmethod
    def verify(self) -> None:
        """Fails unless the owner can administer this storage."""

    @abstractmethod
    def publish(self, encrypted_asset_file) -> None:
        """Puts the ciphertext, read from an open file, where a workload can
        fetch it."""

    @abstractmethod
    def permit(self, identities: List[str]) -> None:
        """Replaces the workload identities allowed to read the ciphertext."""

    @abstractmethod
    def workload_config(self) -> dict:
        """What the workload is told, so it can fetch the ciphertext.

        Travels to the confidential VM as environment the operator can read, so
        it must carry no secrets."""

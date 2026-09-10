"""A backend that keeps everything in a directory on this machine.

For developing and testing the confidential computing flow without a cloud
account. Every step a real backend takes is taken here too -- the asset is
encrypted, the key is stored apart from it, the permitted identities are
written down and checked -- so the code under test is the same code.

What is deliberately *not* here is any security. Nothing is attested, nothing is
verified, and the key sits next to the ciphertext. Selecting `mock` is selecting
"no protection at all", which is why it has to be asked for by name: no
configuration falls back to it.
"""

import json
import os
import tempfile
from typing import List, Optional

from pydantic import BaseModel

MOCK = "mock"

PERMITTED_FILE = "permitted_identities.json"


class MockConfig(BaseModel):
    """`root` is shared by every party on this machine, which is what lets the
    asset owner, the operator and the workload see each other's files."""

    root: str = os.path.join(tempfile.gettempdir(), "medperf_cc_mock")

    class Config:
        extra = "ignore"


class MockStore:
    """A directory per asset, under a root every party agrees on."""

    def __init__(self, config: dict, name: str):
        self.config = MockConfig(**config)
        self.name = name

    @property
    def directory(self) -> str:
        return os.path.join(self.config.root, self.name)

    def path(self, filename: str) -> str:
        return os.path.join(self.directory, filename)

    def write(self, filename: str, content: bytes) -> None:
        os.makedirs(self.directory, exist_ok=True)
        with open(self.path(filename), "wb") as f:
            f.write(content)

    def write_stream(self, filename: str, source) -> None:
        os.makedirs(self.directory, exist_ok=True)
        with open(self.path(filename), "wb") as f:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                f.write(chunk)

    def read(self, filename: str) -> Optional[bytes]:
        if not os.path.exists(self.path(filename)):
            return None
        with open(self.path(filename), "rb") as f:
            return f.read()

    def exists(self, filename: str) -> bool:
        return os.path.exists(self.path(filename))

    def set_permitted(self, identities: List[str]) -> None:
        """Recorded and never enforced.

        Nothing reads this back: the mock workload opens the key file because
        it is there. A real backend releases the key only against an
        attestation matching one of these identities, so this is written to
        show what would have been checked -- and it means the mock exercises
        none of the authorization logic."""
        self.write(PERMITTED_FILE, json.dumps(sorted(identities)).encode())

    def permitted(self) -> List[str]:
        recorded = self.read(PERMITTED_FILE)
        return json.loads(recorded) if recorded else []

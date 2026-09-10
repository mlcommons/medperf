"""Reading what the mock backends left in a directory on this machine.

The workload side of `medperf_cc`'s mock backends: the same files, in the same
places.

The key is released only to a workload whose identity the asset owner
permitted, which is the same rule every real backend applies -- but here the
workload states that identity rather than proving it, so it is a rehearsal of
the check, not the check itself. Selecting `mock` already said nothing is
protected. What it buys is that a grant covering the wrong thing, or nothing,
fails here instead of silently working.
"""

import json
import os
import shutil

ASSET_FILE = "asset.enc"
KEY_FILE = "key.bin"
RESULTS_FILE = "results.enc"
RESULTS_KEY_FILE = "results_key.enc"

# Written by `medperf_cc.backends.mock`; the two names have to agree.
PERMITTED_FILE = "permitted_identities.json"

# Where each term of an identity comes from. The three `EXPECTED_*` values are
# the operator-supplied environment every backend matches an attestation
# against; the script is what a launcher would have measured, and under the
# mock runner it is handed over instead.
TERM_ENV = {
    "script": "MEDPERF_MOCK_ATTESTED_SCRIPT",
    "data": "EXPECTED_DATA_HASH",
    "model": "EXPECTED_MODEL_HASH",
    "collector": "EXPECTED_RESULT_COLLECTOR_HASH",
}


def asset_directory(root: str, name: str) -> str:
    return os.path.join(root, name)


class MockStorage:
    def __init__(self, storage_config_dict: dict):
        self.directory = asset_directory(
            storage_config_dict["root"], storage_config_dict["asset_name"]
        )

    def initialize(self) -> None:
        pass

    def get_asset(self, output_path: str) -> None:
        shutil.copyfile(os.path.join(self.directory, ASSET_FILE), output_path)


class MockVault:
    def __init__(self, vault_config_dict: dict):
        self.directory = asset_directory(
            vault_config_dict["root"], vault_config_dict["asset_name"]
        )
        self.terms = vault_config_dict.get("terms", [])

    def initialize(self) -> None:
        pass

    def get_key(self, output_path: str) -> None:
        self.__check_permitted()
        shutil.copyfile(os.path.join(self.directory, KEY_FILE), output_path)

    def __check_permitted(self) -> None:
        """Refuses a key this workload's identity was not granted.

        The owner wrote down the identities they authorized, projected onto the
        terms they pin. Projecting this workload the same way and looking for it
        is what a real backend does against an attestation."""
        identity = "::".join(os.getenv(TERM_ENV[term], "") for term in self.terms)
        permitted = self.__permitted()
        if identity not in permitted:
            raise RuntimeError(
                f"This workload is not permitted to open the asset in"
                f" {self.directory}. It is running as {identity!r}, and the"
                f" owner authorized {permitted}."
            )

    def __permitted(self):
        path = os.path.join(self.directory, PERMITTED_FILE)
        if not os.path.exists(path):
            raise RuntimeError(
                f"The asset in {self.directory} has no permitted identities"
                " recorded, so nothing may open it. Sync its policy first."
            )
        with open(path) as f:
            return json.load(f)


class MockResult:
    def __init__(self, result_config_dict: dict):
        self.directory = asset_directory(
            result_config_dict["root"], result_config_dict["results_name"]
        )

    def initialize(self) -> None:
        os.makedirs(self.directory, exist_ok=True)

    def write_result(self, result_path: str) -> None:
        shutil.copyfile(result_path, os.path.join(self.directory, RESULTS_FILE))

    def write_key(self, key_bytes: bytes) -> None:
        with open(os.path.join(self.directory, RESULTS_KEY_FILE), "wb") as f:
            f.write(key_bytes)

    def do_test(self, test_data: bytes) -> None:
        """Proves the workload can write where the operator will look, before
        spending the run finding out that it cannot."""
        os.makedirs(self.directory, exist_ok=True)
        probe = os.path.join(self.directory, "write_probe")
        with open(probe, "wb") as f:
            f.write(test_data)
        os.remove(probe)

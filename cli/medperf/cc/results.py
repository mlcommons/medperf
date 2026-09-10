"""Picking up what a confidential workload left, and opening it.

The collector's side. Decryption happens here rather than inside `medperf_cc`
for the same reason encryption does: the private key that opens the results
belongs to the client, and to this client in particular -- an operator who is
somebody else holds neither the key nor the credentials for the store.

Shared by the two ways results get collected: inline, when whoever ran the
workload is also who it was run for, and afterwards, when they are not.
"""

import logging
import os
from time import time
from typing import Optional, Tuple

import yaml

import medperf.config as medperf_config
from medperf.cc.config import result_store_for
from medperf.cc.errors import as_medperf_error
from medperf.commands.certificate.utils import load_user_private_key
from medperf.encryption import AsymmetricEncryption, SymmetricEncryption
from medperf.entities.user import User
from medperf.enums import CryptoKeyType
from medperf.exceptions import DecryptionError, ExecutionError
from medperf.utils import (
    generate_tmp_path,
    remove_path,
    secure_write_to_file,
    tmp_path_for_cc_asset_key,
    untar,
)
from medperf_cc import ResultStore, WorkloadIdentity
from medperf_cc.proof import IntegrityProof


@as_medperf_error()
def setup_collector(user: User):
    """Checks this user can actually receive results where they said.

    The mirror of `setup_operator`: whoever runs the workload needs a machine,
    whoever the results are for needs somewhere to receive them."""
    if not user.cc_collector.configured:
        return

    result_store_for(user.cc_collector.config).verify()


@as_medperf_error(ExecutionError)
def results_exist(result_store: ResultStore, workload: WorkloadIdentity) -> bool:
    return result_store.results_ready(workload)


@as_medperf_error(ExecutionError)
def download_metrics(
    result_store: ResultStore, workload: WorkloadIdentity, execution_id: int
) -> Tuple[dict, Optional[IntegrityProof]]:
    """Downloads one execution's results and reads what is inside them.

    Returns the metrics as the server will hold them, and the integrity proof
    if the workload produced one. Each attempt lands in a directory of its own
    so a second collection cannot overwrite the first."""
    results_path = __attempt_directory(execution_id)
    download_result_files(result_store, workload, results_path)

    # The workload tars the contents of its results directory, so what lands
    # here is those files, not a directory containing them.
    results = {}
    results_file = os.path.join(results_path, medperf_config.results_filename)
    if os.path.exists(results_file):
        with open(results_file) as f:
            results = yaml.safe_load(f)

    proof = IntegrityProof.from_results_dir(results_path)
    if proof is None:
        logging.warning(
            "The workload produced no integrity proof;"
            " these results cannot be verified."
        )
    return results, proof


@as_medperf_error(ExecutionError)
def download_result_files(
    result_store: ResultStore, workload: WorkloadIdentity, results_path: str
) -> None:
    """Downloads one workload's output and unpacks it, leaving it as files.

    What `download_metrics` does before it looks inside. An inference_script
    run wants only this: predictions to be scored on-prem, with no results.yaml
    to read and no proof to pair with metrics."""
    medperf_config.ui.text = "Downloading results..."
    private_key_bytes = load_user_private_key(CryptoKeyType.RSA)
    if private_key_bytes is None:
        raise DecryptionError("Missing Private Key")

    encrypted_results_path = generate_tmp_path()
    encrypted_key = result_store.fetch(workload, encrypted_results_path)

    medperf_config.ui.text = "Decrypting results"
    decryption_key = AsymmetricEncryption().decrypt(private_key_bytes, encrypted_key)

    results_archive_path = generate_tmp_path()
    tmp_key_path = tmp_path_for_cc_asset_key()
    secure_write_to_file(tmp_key_path, decryption_key)
    SymmetricEncryption().decrypt_file(
        encrypted_results_path, tmp_key_path, results_archive_path
    )
    remove_path(tmp_key_path, sensitive=True)
    del decryption_key

    medperf_config.ui.text = "Uncompressing results"
    untar(results_archive_path, remove=True, extract_to=results_path)


def __attempt_directory(execution_id: int) -> str:
    timestamp = str(time()).replace(".", "_")
    return os.path.join(
        medperf_config.script_result_folder, str(execution_id), timestamp
    )

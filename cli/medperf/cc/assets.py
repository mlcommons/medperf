"""Preparing a dataset or a model for confidential execution.

Encryption happens here rather than inside `medperf_cc`: the key is the asset
owner's, so it never has to leave the client. What the components downstream do
is transport the ciphertext and enforce which workloads may have the key.
"""

import os

from tqdm import tqdm

from medperf import config as medperf_config
from medperf.cc.config import asset_for
from medperf.cc.errors import as_medperf_error
from medperf.encryption import SymmetricEncryption
from medperf.entities.dataset import Dataset
from medperf.entities.model import Model
from medperf.exceptions import MedperfException
from medperf.utils import (
    generate_tmp_path,
    remove_path,
    secure_write_to_file,
    tar,
    tmp_path_for_cc_asset_key,
)
from medperf_cc import (
    AssetKind,
    ConfidentialAsset,
    WorkloadGrant,
    generate_encryption_key,
)


@as_medperf_error()
def setup_dataset_for_cc(dataset: Dataset):
    if not dataset.is_cc_configured():
        return

    asset = asset_for(dataset, AssetKind.DATA)
    medperf_config.ui.text = "Verifying the confidential computing environment"
    asset.verify()

    medperf_config.ui.text = "Compressing dataset"
    asset_path = generate_tmp_path()
    tar(asset_path, [dataset.data_path, dataset.labels_path])
    __publish(asset, asset_path)
    remove_path(asset_path)


@as_medperf_error()
def setup_model_for_cc(model: Model):
    if not model.is_cc_configured():
        return
    __require_asset_model(model)

    asset = asset_for(model, AssetKind.MODEL)
    medperf_config.ui.text = "Verifying the confidential computing environment"
    asset.verify()

    __publish(asset, model.asset_obj.get_archive_path())


@as_medperf_error()
def set_permitted_grants(entity, kind: AssetKind, grants: list[WorkloadGrant]):
    if kind is AssetKind.MODEL:
        __require_asset_model(entity)

    if not grants:
        # Correct when every association really has gone away, and a silent
        # disaster when it is only that a peer has not uploaded a certificate
        # yet. The two are indistinguishable from here, so say what happened
        # rather than report a successful sync either way.
        medperf_config.ui.print_warning(
            "No workload is authorized to open this asset, so this sync"
            " withdraws every grant it had. This is expected if its"
            " associations were rejected; otherwise check that the other"
            " parties hold certificates."
        )

    asset_for(entity, kind).set_permitted(grants)


def sync_cc_metadata(entity, update_comms_fn):
    """Records on the server that the entity's policy is now up to date.

    Called after the policy has been written, so a failure here leaves the
    server thinking the policy is staler than it is — the safe direction."""
    entity.set_last_synced()
    body = {"user_metadata": entity.user_metadata}
    update_comms_fn(entity.id, body)


def __require_asset_model(model: Model):
    if not model.is_asset():
        raise MedperfException(
            f"Model {model.id} is not a file-based asset and cannot be set up for confidential computing."
        )


def __publish(asset: ConfidentialAsset, asset_path: str):
    medperf_config.ui.text = "Generating encryption key"
    encryption_key = generate_encryption_key()

    medperf_config.ui.text = "Encrypting asset locally"
    encrypted_asset_path = __encrypt_asset(asset_path, encryption_key)

    medperf_config.ui.text = "Publishing the encrypted asset and its key"
    with open(encrypted_asset_path, "rb") as in_file:
        with __upload_progress(in_file) as file_obj:
            asset.publish(encryption_key, file_obj)
    del encryption_key
    remove_path(encrypted_asset_path)


def __encrypt_asset(asset_path: str, encryption_key: bytes) -> str:
    encrypted_asset_path = generate_tmp_path()
    encryption_key_file = tmp_path_for_cc_asset_key()
    secure_write_to_file(encryption_key_file, encryption_key)
    SymmetricEncryption().encrypt_file(
        asset_path, encryption_key_file, encrypted_asset_path
    )
    remove_path(encryption_key_file, sensitive=True)
    return encrypted_asset_path


def __upload_progress(in_file):
    """Wraps a file so that reading it reports progress through the UI."""
    return tqdm.wrapattr(
        in_file,
        "read",
        total=get_file_size(in_file),
        miniters=1,
        desc="Uploading the encrypted asset",
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
        file=UIWriter(),
    )


class UIWriter:
    """A file-like object that lets tqdm write through config.ui"""

    def write(self, msg):
        medperf_config.ui.print(msg)

    def flush(self):
        pass


def get_file_size(file_object) -> int:
    """Get the size of a file in bytes."""
    try:
        total_bytes = os.fstat(file_object.fileno()).st_size
    except (AttributeError, OSError):
        total_bytes = None
    return total_bytes

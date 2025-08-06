from __future__ import annotations
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from dataclasses import dataclass
import os
from typing import TYPE_CHECKING

from medperf import config
from medperf.exceptions import MissingPrivateKeyException
from medperf.utils import remove_path, get_pki_assets_path
from medperf.account_management.account_management import get_medperf_user_data

if TYPE_CHECKING:
    from medperf.entities.ca import CA
    from medperf.entities.cube import Cube


@dataclass
class PrivateKeyDecryptionInfo:
    private_key: rsa.RSAPrivateKey
    padding: padding.AsymmetricPadding


def load_encrypted_symmetric_key_and_delete(encrypted_key_file_path: str) -> bytes:
    with open(encrypted_key_file_path, "rb") as f:
        encrypted_key = f.read()
    remove_path(encrypted_key_file_path)
    return encrypted_key


def load_private_key_info(ca: CA, container: Cube) -> PrivateKeyDecryptionInfo:
    # TODO validate configs!
    # Are we doing PEM Private Keys, with no password and default_backend as implemented?
    # Are we going to support multiple configurations? If so, how?
    # What about padding? We a default, support multiple? If supporting multiple, how to config?

    user_email = get_medperf_user_data["email"]
    pki_assets_dir = get_pki_assets_path(common_name=user_email, ca_name=ca.name)
    private_key_path = os.path.join(pki_assets_dir, config.private_key_file)

    if not os.path.exists(private_key_path):
        error_msg = (
            f"No private key was found locally for the user email {user_email} and "
            f"Certificate Authority (CA) {ca.name} (UID: {ca.id}), which enables "
            f"access to the Model Container {container.name} (UID: {container.id}).\n"
            f"Please run the following command to obtain a private key:\n"
            f"medperf certificate get_client_certificate --container-id {container.id}"
        )
        raise MissingPrivateKeyException(error_msg)

    with open(private_key_path, "rb") as private_key_file:
        private_bytes = private_key_file.read()

    private_key = serialization.load_pem_private_key(
        data=private_bytes, backend=default_backend(), password=None
    )
    padding_obj = padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None,
    )

    private_info = PrivateKeyDecryptionInfo(
        private_key=private_key, padding=padding_obj
    )
    return private_info

from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.fernet import Fernet
from medperf.utils import remove_path


@dataclass
class PrivateKeyDecryptionInfo:
    private_key: rsa.RSAPrivateKey
    padding: padding.AsymmetricPadding


def load_encrypted_symmetric_key_and_delete() -> bytes:
    encrypted_key_file_path = "implement/where/this/comes/from"
    with open(encrypted_key_file_path, "rb") as f:
        encrypted_key = f.read()
    remove_path(encrypted_key_file_path)
    return encrypted_key


def load_private_key_info(private_key_path: str) -> PrivateKeyDecryptionInfo:
    # TODO validate configs!
    # Are we doing PEM Private Keys, with no password and default_backend as implemented?
    # Are we going to support multiple configurations? If so, how?
    # What about padding? We a default, support multiple? If supporting multiple, how to config?
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


def _decrypt_encrypted_symmetric_key(
    encrypted_symmetric_key: bytes,
    private_key: PrivateKeyDecryptionInfo,
) -> Fernet:
    # TODO validate configs!
    # Are we going to use AES with GCM mode? Something else? Allow configs?
    # Are going to use associated_data?
    decrypted_key = private_key.private_key.decrypt(
        ciphertext=encrypted_symmetric_key,
        padding=private_key.padding,
    )
    fernet_obj = Fernet(decrypted_key)
    return fernet_obj


def decrypt_image(
    encrypted_image_path: str,
    decrypted_image_path: str,
    encrypted_symmetric_key: bytes,
    private_key_info: PrivateKeyDecryptionInfo,
) -> str:
    decryptor = _decrypt_encrypted_symmetric_key(
        encrypted_symmetric_key=encrypted_symmetric_key,
        private_key=private_key_info,
    )

    with (
        open(encrypted_image_path, "rb") as encrypted_f,
        open(decrypted_image_path, "wb") as decrypted_f,
    ):
        decrypted_bytes = decryptor.decrypt(encrypted_f.read())
        decrypted_f.write(decrypted_bytes)

    return decrypted_image_path

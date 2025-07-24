from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers import (
    Cipher,
    algorithms,
    modes,
    CipherContext,
)
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from medperf import config
from typing import Union


@dataclass
class SymmetricKeyInfo:
    """
    For symmetric encryption (used to encrypt/decrypt container images) we need 3 inputs for decryption:
    - the key. This will come encrypted with some type of assymetric (ie public/private key). THIS IS A SECRET!!!
    - the nonce (number once). This is a byte string that is used along with the key to encrypt and decrypt the image.
      The nounce is not a secret and will not come encrypted. There are nuances with regarding encryption (nonces cannot
      be reused with the same key, hence the "number ONCE") but for decryption, we simply need the nonce used for encryption.
      This is NOT a secret.
    - the encryption tag. This is necessary for decrypting when doing the file in chunks, which we do here because container
      images can get quite big! This is NOT a secret.
    - associated_data
    """

    encrypted_key: bytes
    nonce: bytes
    tag: bytes
    associated_data: Union[bytes, None] = None


@dataclass
class PrivateKeyDecryptionInfo:
    private_key: rsa.RSAPrivateKey
    padding: padding.AsymmetricPadding


def _load_file_as_bytes(file_path: str) -> bytes:
    with open(file_path, "rb") as f:
        byte_content = f.read()

    return byte_content


def load_encrypted_symmetric_key_info(
    encrypted_key_file_path: str, nonce_file_path: str, tag_file_path: str
) -> SymmetricKeyInfo:
    encrypted_key = _load_file_as_bytes(encrypted_key_file_path)
    nonce = _load_file_as_bytes(nonce_file_path)
    tag = _load_file_as_bytes(tag_file_path)
    return SymmetricKeyInfo(encrypted_key=encrypted_key, nonce=nonce, tag=tag)


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
        mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256, label=None
    )

    private_info = PrivateKeyDecryptionInfo(
        private_key=private_key, padding=padding_obj
    )
    return private_info


def _decrypt_encrypted_symmetric_key(
    encrypted_symmetric_key_info: SymmetricKeyInfo,
    private_key: PrivateKeyDecryptionInfo,
) -> CipherContext:
    # TODO validate configs!
    # Are we going to use AES with GCM mode? Something else? Allow configs?
    # Are going to use associated_data?
    decrypted_key = private_key.private_key.decrypt(
        ciphertext=encrypted_symmetric_key_info.encrypted_key,
        padding=private_key.padding,
    )
    decryptor = Cipher(
        algorithm=algorithms.AES(decrypted_key),
        mode=modes.GCM(
            initialization_vector=encrypted_symmetric_key_info.nonce,
            tag=encrypted_symmetric_key_info.tag,
        ),
    ).decryptor()
    decryptor.authenticate_additional_data(encrypted_symmetric_key_info.associated_data)
    return decryptor


def decrypt_image(
    encrypted_image_path: str,
    decrypted_image_path: str,
    encrypted_symmetric_key_info: SymmetricKeyInfo,
    private_key_info: PrivateKeyDecryptionInfo,
) -> str:
    decryptor = _decrypt_encrypted_symmetric_key(
        encrypted_symmetric_key_info=encrypted_symmetric_key_info,
        private_key=private_key_info,
    )

    with (
        open(encrypted_image_path, "rb") as encrypted_f,
        open(decrypted_image_path, "wb") as decrypted_f,
    ):
        decrypting = True
        while decrypting:
            encrypted_data = encrypted_f.read(config.block_size)
            if encrypted_data == b"":
                decrypted_data = decryptor.finalize()
                decrypting = False
            else:
                decrypted_data = decryptor.update(encrypted_data)
            decrypted_f.write(decrypted_data)

    return decrypted_image_path

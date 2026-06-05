import os
import secrets
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography import x509
import logging
import hashlib
from utils import run_command


def generate_encryption_key(encryption_key_file: str):
    with open(encryption_key_file, "wb") as f:
        pass
    os.chmod(encryption_key_file, 0o700)
    with open(encryption_key_file, "ab") as f:
        f.write(secrets.token_bytes(32))


def get_string_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def get_file_hash(path: str) -> str:
    logging.debug("Calculating hash for file {}".format(path))
    BUF_SIZE = 65536
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha.update(data)

    sha_val = sha.hexdigest()
    logging.debug(f"Hash for file {path}: {sha_val}")
    return sha_val


def get_folders_hash(paths: list[str]) -> str:
    """Generates a hash for all the contents of the fiven folders. This procedure
    hashes all the files in all passed folders, sorts them and then hashes that list.

    Args:
        paths List(str): Folders to hash.

    Returns:
        str: sha256 hash that represents all the folders altogether
    """
    hashes = []

    # The hash doesn't depend on the order of paths or folders, as the hashes get sorted after the fact
    for path in paths:
        for root, _, files in os.walk(path, topdown=False):
            for file in files:
                logging.debug(f"Hashing file {file}")
                filepath = os.path.join(root, file)
                hashes.append(get_file_hash(filepath))

    hashes = sorted(hashes)
    sha = hashlib.sha256()
    for hash in hashes:
        sha.update(hash.encode("utf-8"))
    hash_val = sha.hexdigest()
    logging.debug(f"Folder hash: {hash_val}")
    return hash_val


# symmetric encryption/decryption
class SymmetricEncryption:
    def __init__(self):
        self.gpg_exec = "gpg"

    def check(self) -> None:
        logging.debug("Checking if GPG is available")
        gpg_check_command = [self.gpg_exec, "--version"]
        logging.debug("Running GPG check command")
        run_command(gpg_check_command)

    def decrypt_file(
        self, encrypted_file_path: str, decryption_key_file: str, output_path: str
    ) -> None:
        logging.debug("Decrypting a GPG file")
        logging.debug(f"Encrypted file path: {encrypted_file_path}")
        logging.debug(f"Output path: {output_path}")
        logging.debug(f"Decryption key file path: {decryption_key_file}")
        if os.path.exists(output_path):
            raise RuntimeError(
                f"Output file for decryption {output_path} already exists"
            )
        gpg_decrypt_command = [
            self.gpg_exec,
            "--batch",
            "--decrypt",
            "--output",
            output_path,
            "--passphrase-file",
            decryption_key_file,
            encrypted_file_path,
        ]
        run_command(gpg_decrypt_command)

    def encrypt_file(
        self, plaintext_file_path: str, decryption_key_file: str, output_path: str
    ) -> None:
        logging.debug("Encrypting a file with GPG")
        logging.debug(f"Plaintext file path: {plaintext_file_path}")
        logging.debug(f"Output path: {output_path}")
        logging.debug(f"Decryption key file path: {decryption_key_file}")
        if os.path.exists(output_path):
            raise RuntimeError(
                f"Output file for encryption {output_path} already exists"
            )
        gpg_encrypt_command = [
            self.gpg_exec,
            "--batch",
            "--symmetric",
            "--output",
            output_path,
            "--passphrase-file",
            decryption_key_file,
            plaintext_file_path,
        ]
        run_command(gpg_encrypt_command)


# asymmetric encryption/decryption
class AsymmetricEncryption:
    def __init__(self):
        self.padding = padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        )

    def certificate_encrypt(self, certificate_bytes: bytes, data_bytes: bytes) -> bytes:
        logging.debug("Performing Asymmetric Encryption")
        certificate_obj = x509.load_pem_x509_certificate(data=certificate_bytes)
        public_key_obj = certificate_obj.public_key()
        encrypted_data = public_key_obj.encrypt(data_bytes, padding=self.padding)
        return encrypted_data

    def public_key_encrypt(self, public_key_bytes: bytes, data_bytes: bytes) -> bytes:
        logging.debug("Performing Asymmetric Encryption with a public key")
        public_key_obj = serialization.load_pem_public_key(public_key_bytes)
        encrypted_data = public_key_obj.encrypt(data_bytes, padding=self.padding)
        return encrypted_data

    def decrypt(self, private_key_bytes: bytes, encrypted_data_bytes: bytes) -> bytes:
        logging.debug("Performing Asymmetric Decryption")
        private_key = serialization.load_pem_private_key(
            data=private_key_bytes, password=None
        )
        data_bytes = private_key.decrypt(encrypted_data_bytes, padding=self.padding)
        return data_bytes

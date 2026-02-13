from medperf.exceptions import (
    DecryptionError,
    EncryptionError,
    ExecutionError,
    MedperfException,
)
from medperf.utils import run_command
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography import x509
import logging


# symmetric encryption/decryption
class SymmetricEncryption:
    def __init__(self):
        self.gpg_exec = "gpg"

    def check(self) -> None:
        logging.debug("Checking if GPG is available")
        gpg_check_command = [self.gpg_exec, "--version"]
        logging.debug("Running GPG check command")
        try:
            run_command(gpg_check_command)
        except ExecutionError:
            raise MedperfException("GPG is not installed.")

    def decrypt_file(
        self, encrypted_file_path: str, decryption_key_file: str, output_path: str
    ) -> None:
        logging.debug("Decrypting a GPG file")
        logging.debug(f"Encrypted file path: {encrypted_file_path}")
        logging.debug(f"Output path: {output_path}")
        logging.debug(f"Decryption key file path: {decryption_key_file}")

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
        try:
            logging.debug("Running GPG decrypt command")
            run_command(gpg_decrypt_command)
        except Exception as e:
            raise DecryptionError(f"File decryption failed: {str(e)}")

    def encrypt_file(
        self, plaintext_file_path: str, decryption_key_file: str, output_path: str
    ) -> None:
        logging.debug("Encrypting a file with GPG")
        logging.debug(f"Plaintext file path: {plaintext_file_path}")
        logging.debug(f"Output path: {output_path}")
        logging.debug(f"Decryption key file path: {decryption_key_file}")

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
        try:
            logging.debug("Running GPG encrypt command")
            run_command(gpg_encrypt_command)
        except Exception as e:
            raise DecryptionError(f"File encryption failed: {str(e)}")


# asymmetric encryption/decryption
class AsymmetricEncryption:
    def __init__(self):
        self.padding = padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        )

    def encrypt(self, certificate_bytes: bytes, data_bytes: bytes) -> bytes:
        logging.debug("Performing Asymmetric Encryption")
        try:
            certificate_obj = x509.load_pem_x509_certificate(data=certificate_bytes)
            public_key_obj = certificate_obj.public_key()
            encrypted_data = public_key_obj.encrypt(data_bytes, padding=self.padding)
            return encrypted_data
        except Exception as e:
            raise EncryptionError(f"Data encryption failed: {str(e)}")

    def decrypt(self, private_key_bytes: bytes, encrypted_data_bytes: bytes) -> bytes:
        logging.debug("Performing Asymmetric Decryption")
        try:
            private_key = serialization.load_pem_private_key(
                data=private_key_bytes, password=None
            )
            data_bytes = private_key.decrypt(encrypted_data_bytes, padding=self.padding)
            return data_bytes
        except Exception as e:
            raise DecryptionError(f"Data decryption failed: {str(e)}")

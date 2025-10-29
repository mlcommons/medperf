from medperf.exceptions import ExecutionError, MedperfException
from medperf.utils import run_command
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography import x509


def check_gpg():
    gpg_check_command = ["gpg", "--version"]
    try:
        run_command(gpg_check_command)
    except ExecutionError:
        raise MedperfException("GPG is not installed.")


# GPG symmetric decryption
def decrypt_gpg_file(encrypted_file_path, decryption_key_file, output_path):
    gpg_decrypt_command = [
        "gpg",
        "--batch",
        "--decrypt",
        "--output",
        output_path,
        "--passphrase-file",
        decryption_key_file,
        encrypted_file_path,
    ]
    try:
        run_command(gpg_decrypt_command)
    except ExecutionError:
        raise MedperfException("File decryption failed")


# asymmetric encryption/decryption
class AsymmetricEncryption:
    def __init__(self):
        self.padding = padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        )

    def encrypt(self, certificate_bytes: bytes, data_bytes: bytes) -> bytes:
        certificate_obj = x509.load_pem_x509_certificate(data=certificate_bytes)
        public_key_obj = certificate_obj.public_key()
        encrypted_data = public_key_obj.encrypt(data_bytes, padding=self.padding)
        return encrypted_data

    def decrypt(self, private_key_bytes: bytes, encrypted_data_bytes: bytes) -> bytes:
        private_key = serialization.load_pem_private_key(
            data=private_key_bytes, password=None
        )
        data_bytes = private_key.decrypt(encrypted_data_bytes, padding=self.padding)
        return data_bytes

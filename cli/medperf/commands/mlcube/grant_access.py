from medperf.entities.certificate import Certificate
from medperf.entities.ca import CA
from cryptography import x509
from medperf.utils import get_container_key_dir_path, approval_prompt
import os
from medperf import config
from medperf.exceptions import MissingContainerKeyException
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from medperf.exceptions import CleanExit
from medperf.certificates import trust
from medperf.entities.encrypted_container_key import EncryptedContainerKey


class GrantAccess:
    @classmethod
    def run(
        cls,
        ca_id: int,
        benchmark_id: int,
        model_id: int,
        name: str = None,
        approved: bool = False,
    ):
        """
        Registers encrypted access keys in the MedPerf server for all
        Data Owners registered to the Benchmark from benchmark_id and
        authorized by the Certificate Authority from ca_id.
        """

        msg = (
            f"Please confirm that you wish to give *ALL* Data Owners "
            f"registered in Benchmark (UID: {benchmark_id}) access to "
            f"the Model (UID: {model_id}).\n"
            f"The Certificate Authority (CA: {ca_id}) is used to authenticate the Data Owners. [Y/n]"
        )

        if not approved and not approval_prompt(msg):
            raise CleanExit("Access granting operation cancelled")

        if name is None:
            name = f"Model {model_id} Key"
        config.ui.print("Verifying Certificate Authority")
        ca = CA.get(uid=ca_id)
        trust(ca)

        config.ui.print("Getting the local decryption key")
        container_key_bytes = cls.get_container_key_bytes(
            model_id=model_id, ca_name=ca.name
        )

        config.ui.print("Getting Data Owner Certificates")
        certificates = Certificate.get_list_from_benchmark_model_ca(
            ca_id=ca_id, benchmark_id=benchmark_id, model_id=model_id
        )

        config.ui.print("Creating Encrypted Keys for Data Owners")
        encrypted_key_info_list = cls.generate_encrypted_keys_list(
            certificates=certificates,
            container_key_bytes=container_key_bytes,
            key_name=name,
        )

        config.ui.print("Uploading Encrypted Keys")
        EncryptedContainerKey.upload_many(
            encrypted_key_info_list,
            model_id=model_id,
            ca_id=ca_id,
        )

    @classmethod
    def _encrypt_public_key_from_certificate(
        cls,
        certificate_bytes: bytes,
        container_key_bytes: bytes,
        padding: padding.AsymmetricPadding,
    ) -> str:
        certificate_obj = x509.load_pem_x509_certificate(data=certificate_bytes)
        public_key_obj = certificate_obj.public_key()
        encrypted_container_key = public_key_obj.encrypt(
            container_key_bytes, padding=padding
        )
        return encrypted_container_key

    @staticmethod
    def get_container_key_bytes(model_id: int, ca_name: str):
        container_key_file = os.path.join(
            get_container_key_dir_path(container_id=model_id, ca_name=ca_name),
            config.container_key_file,
        )

        if not os.path.exists(container_key_file):
            raise MissingContainerKeyException(
                f"Local container key for Model UID {model_id} not found!"
            )

        with open(container_key_file, "rb") as f:
            container_key_bytes = f.read()

        return container_key_bytes

    @classmethod
    def generate_encrypted_keys_list(
        cls, container_key_bytes: bytes, key_name: str, certificates: list[Certificate]
    ):
        padding_obj = padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        )
        key_info_list = []
        for certificate in certificates:
            encrypted_key = cls._encrypt_public_key_from_certificate(
                certificate_bytes=certificate.certificate_content,
                container_key_bytes=container_key_bytes,
                padding=padding_obj,
            )
            key_obj = EncryptedContainerKey(
                encrypted_key=encrypted_key, data_owner=certificate.owner, name=key_name
            )
            key_info_list.append(key_obj)

        return key_info_list
